"""Azure Speech helpers. Credentials come from the .env file next to this script."""

import os
import queue
import tempfile
import threading
import wave
from contextlib import contextmanager
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# Voices offered for text to speech; the API only accepts these.
VOICES = {
    "en-US-JennyNeural": "English (US) – Jenny",
    "en-US-GuyNeural": "English (US) – Guy",
    "tr-TR-EmelNeural": "Turkish – Emel",
    "tr-TR-AhmetNeural": "Turkish – Ahmet",
    "de-DE-KatjaNeural": "German – Katja",
    "fr-FR-DeniseNeural": "French – Denise",
    "es-ES-ElviraNeural": "Spanish – Elvira",
}
DEFAULT_VOICE = "en-US-JennyNeural"
MAX_TEXT_LENGTH = 1000

# Spoken languages the page can recognize; the API only accepts these.
LANGUAGES = {
    "en-US": "English (US)",
    "tr-TR": "Turkish",
    "de-DE": "German",
    "fr-FR": "French",
    "es-ES": "Spanish",
}
DEFAULT_LANGUAGE = "en-US"

# Translation targets, and the voice used to read each translation aloud.
TRANSLATION_TARGETS = {
    "en": ("English", "en-US-JennyNeural"),
    "tr": ("Turkish", "tr-TR-EmelNeural"),
    "de": ("German", "de-DE-KatjaNeural"),
    "fr": ("French", "fr-FR-DeniseNeural"),
    "es": ("Spanish", "es-ES-ElviraNeural"),
}

# Pronunciation assessment with prosody is only available for English (US).
PRONUNCIATION_LANGUAGE = "en-US"
MAX_REFERENCE_LENGTH = 300

# Stop waiting for Azure after this many seconds, so a request can never hang forever.
RECOGNITION_TIMEOUT_SECONDS = 120


class SpeechConfigError(Exception):
    """Raised when the Azure key or region is missing from .env."""


class SpeechServiceError(Exception):
    """Raised when Azure could not complete the request."""


class NoSpeechError(Exception):
    """Raised when the audio was valid but contained no recognizable speech."""


# --- Shared helpers ---

def _credentials():
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    if not key or not region:
        raise SpeechConfigError("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in Week-5-Task-1/.env.")
    return key, region


def _speech_config():
    key, region = _credentials()
    return speechsdk.SpeechConfig(subscription=key, region=region)


def _check_language(language, allowed):
    if language not in allowed:
        raise ValueError(f"Unknown language '{language}'.")


def _check_wav(path):
    """Raise ValueError unless the file is a 16-bit PCM WAV that Azure can read."""
    try:
        with wave.open(str(path), "rb") as wav:
            if wav.getsampwidth() != 2:
                raise ValueError("WAV audio must be 16-bit PCM.")
            if wav.getnframes() == 0:
                raise ValueError("The audio file is empty.")
    except (wave.Error, EOFError):
        raise ValueError("Audio must be a WAV file (the page converts recordings and uploads for you).")


@contextmanager
def _wav_file(wav_bytes):
    """Write uploaded WAV bytes to a checked temporary file and delete it afterwards.

    The Azure SDK reads audio from a file path, not from bytes in memory.
    """
    if not wav_bytes:
        raise ValueError("Please record or choose an audio file.")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
        temp.write(wav_bytes)
        path = Path(temp.name)
    try:
        _check_wav(path)
        yield str(path)
    finally:
        path.unlink(missing_ok=True)


def _run_continuous(recognizer, start, stop, on_result):
    """Run a continuous recognizer until the audio ends, calling on_result for each phrase.

    start and stop are the recognizer's own start/stop methods, because
    SpeechRecognizer, TranslationRecognizer and ConversationTranscriber name
    them differently.
    """
    errors = []
    done = threading.Event()

    def on_canceled(event):
        # EndOfStream is the normal end of a file; only Error is a real failure.
        if event.reason == speechsdk.CancellationReason.Error:
            errors.append(event.error_details)
        done.set()

    on_result_event = recognizer.transcribed if hasattr(recognizer, "transcribed") else recognizer.recognized
    on_result_event.connect(on_result)
    recognizer.canceled.connect(on_canceled)
    recognizer.session_stopped.connect(lambda event: done.set())

    start()
    finished = done.wait(RECOGNITION_TIMEOUT_SECONDS)
    stop()

    if errors:
        raise SpeechServiceError(f"Azure could not process the audio: {errors[0]}")
    if not finished:
        raise SpeechServiceError("Azure took too long to process the audio.")


# --- Text to speech ---

def synthesize(text, voice=DEFAULT_VOICE):
    """Turn text into speech and return it as WAV bytes.

    Raises:
        ValueError: If the text is empty or too long, or the voice is unknown.
        SpeechConfigError: If the Azure credentials are missing.
        SpeechServiceError: If Azure rejects or cancels the request.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Please enter some text.")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Text is too long (max {MAX_TEXT_LENGTH} characters).")
    if voice not in VOICES:
        raise ValueError(f"Unknown voice '{voice}'.")

    config = _speech_config()
    config.speech_synthesis_voice_name = voice
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    )
    # audio_config=None keeps the audio in memory instead of playing it on the server's speakers.
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = synthesizer.speak_text_async(text.strip()).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    details = result.cancellation_details
    raise SpeechServiceError(f"Azure could not synthesize the text: {details.error_details or details.reason}")


# --- Speech to text ---

def transcribe(wav_bytes, language=DEFAULT_LANGUAGE):
    """Turn WAV audio into text and return it.

    Uses continuous recognition, so recordings longer than one sentence are
    transcribed completely, not just their first phrase.

    Raises:
        ValueError: If the audio is not a usable WAV file or the language is unknown.
        SpeechConfigError: If the Azure credentials are missing.
        SpeechServiceError: If Azure rejects the request or times out.
        NoSpeechError: If no speech was recognized.
    """
    _check_language(language, LANGUAGES)
    config = _speech_config()
    phrases = []

    def on_recognized(event):
        if event.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            phrases.append(event.result.text)

    with _wav_file(wav_bytes) as path:
        audio_config = speechsdk.audio.AudioConfig(filename=path)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=config, audio_config=audio_config, language=language
        )
        _run_continuous(
            recognizer,
            recognizer.start_continuous_recognition,
            recognizer.stop_continuous_recognition,
            on_recognized,
        )
        # Release the SDK's handle on the file before it is deleted.
        del recognizer, audio_config

    text = " ".join(phrases).strip()
    if not text:
        raise NoSpeechError("No speech could be recognized in the audio.")
    return text


# --- Part 4: real-time diarization ---

def diarize(wav_bytes, language=DEFAULT_LANGUAGE):
    """Transcribe audio with speaker labels and yield each phrase as soon as Azure sends it.

    Checks the input first and raises before streaming starts, so the API can
    still answer with a normal error status. After that it yields dictionaries:
    {"speaker": "Guest-1", "text": "..."} for each phrase, then {"done": True},
    or {"error": "..."} if Azure fails midway.
    """
    _check_language(language, LANGUAGES)
    config = _speech_config()
    # Enter the temp-file context now so a bad WAV raises ValueError before streaming.
    wav_context = _wav_file(wav_bytes)
    path = wav_context.__enter__()

    def stream():
        phrases = queue.Queue()
        try:
            audio_config = speechsdk.audio.AudioConfig(filename=path)
            transcriber = speechsdk.transcription.ConversationTranscriber(
                speech_config=config, audio_config=audio_config, language=language
            )

            def on_transcribed(event):
                if event.result.reason == speechsdk.ResultReason.RecognizedSpeech and event.result.text:
                    phrases.put({"speaker": event.result.speaker_id or "Unknown", "text": event.result.text})

            # Run Azure in a background thread so phrases can be sent to the page while it works.
            outcome = {}

            def run():
                try:
                    _run_continuous(
                        transcriber,
                        lambda: transcriber.start_transcribing_async().get(),
                        lambda: transcriber.stop_transcribing_async().get(),
                        on_transcribed,
                    )
                except SpeechServiceError as error:
                    outcome["error"] = str(error)
                finally:
                    phrases.put(None)

            threading.Thread(target=run, daemon=True).start()
            count = 0
            while (phrase := phrases.get()) is not None:
                count += 1
                yield phrase
            if "error" in outcome:
                yield {"error": outcome["error"]}
            elif count == 0:
                yield {"error": "No speech could be recognized in the audio."}
            else:
                yield {"done": True}
            del transcriber, audio_config
        finally:
            wav_context.__exit__(None, None, None)

    return stream()


# --- Part 4: speech translation ---

def translate(wav_bytes, source_language=DEFAULT_LANGUAGE, target_language="tr"):
    """Recognize speech in source_language and translate it into target_language.

    Returns:
        {"recognized": original text, "translation": translated text,
         "voice": a voice that can read the translation aloud}

    Raises:
        ValueError, SpeechConfigError, SpeechServiceError, NoSpeechError: as in transcribe().
    """
    _check_language(source_language, LANGUAGES)
    if target_language not in TRANSLATION_TARGETS:
        raise ValueError(f"Unknown target language '{target_language}'.")
    if source_language.split("-")[0] == target_language:
        raise ValueError("Choose a target language different from the spoken language.")

    key, region = _credentials()
    config = speechsdk.translation.SpeechTranslationConfig(subscription=key, region=region)
    config.speech_recognition_language = source_language
    config.add_target_language(target_language)

    recognized, translated = [], []

    def on_recognized(event):
        if event.result.reason == speechsdk.ResultReason.TranslatedSpeech:
            recognized.append(event.result.text)
            translated.append(event.result.translations.get(target_language, ""))

    with _wav_file(wav_bytes) as path:
        audio_config = speechsdk.audio.AudioConfig(filename=path)
        recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=config, audio_config=audio_config
        )
        _run_continuous(
            recognizer,
            recognizer.start_continuous_recognition,
            recognizer.stop_continuous_recognition,
            on_recognized,
        )
        del recognizer, audio_config

    if not "".join(recognized).strip():
        raise NoSpeechError("No speech could be recognized in the audio.")
    return {
        "recognized": " ".join(recognized).strip(),
        "translation": " ".join(translated).strip(),
        "voice": TRANSLATION_TARGETS[target_language][1],
    }


# --- Part 4: pronunciation assessment ---

def assess_pronunciation(wav_bytes, reference_text):
    """Score how well the audio matches reference_text, read aloud in English.

    Returns:
        {"recognized": what Azure heard,
         "scores": {"pronunciation", "accuracy", "fluency", "completeness", "prosody"},
         "words": [{"word", "accuracy", "error"}, ...]}
        Scores are 0–100. error is "None", "Mispronunciation", "Omission",
        "Insertion", and so on, as reported by Azure.

    Raises:
        ValueError, SpeechConfigError, SpeechServiceError, NoSpeechError: as in transcribe().
    """
    if not isinstance(reference_text, str) or not reference_text.strip():
        raise ValueError("Please enter the sentence to read aloud.")
    if len(reference_text) > MAX_REFERENCE_LENGTH:
        raise ValueError(f"Reference text is too long (max {MAX_REFERENCE_LENGTH} characters).")

    config = _speech_config()
    assessment = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text.strip(),
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Word,
        # Miscue detection marks words that were skipped or added compared to the reference.
        enable_miscue=True,
    )
    assessment.enable_prosody_assessment()

    with _wav_file(wav_bytes) as path:
        audio_config = speechsdk.audio.AudioConfig(filename=path)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=config, audio_config=audio_config, language=PRONUNCIATION_LANGUAGE
        )
        assessment.apply_to(recognizer)
        # One sentence is read, so a single recognition is enough.
        result = recognizer.recognize_once()
        del recognizer, audio_config

    if result.reason == speechsdk.ResultReason.NoMatch:
        raise NoSpeechError("No speech could be recognized in the audio.")
    if result.reason == speechsdk.ResultReason.Canceled:
        details = result.cancellation_details
        raise SpeechServiceError(f"Azure could not assess the audio: {details.error_details or details.reason}")

    scores = speechsdk.PronunciationAssessmentResult(result)
    return {
        "recognized": result.text,
        "scores": {
            "pronunciation": scores.pronunciation_score,
            "accuracy": scores.accuracy_score,
            "fluency": scores.fluency_score,
            "completeness": scores.completeness_score,
            "prosody": scores.prosody_score,
        },
        "words": [
            {"word": word.word, "accuracy": word.accuracy_score, "error": word.error_type}
            for word in scores.words
        ],
    }
