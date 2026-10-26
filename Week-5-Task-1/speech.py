"""Azure Speech helpers. Credentials come from the .env file next to this script."""

import os
import tempfile
import threading
import wave
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
}
DEFAULT_VOICE = "en-US-JennyNeural"
MAX_TEXT_LENGTH = 1000

# Languages offered for speech to text; the API only accepts these.
LANGUAGES = {
    "en-US": "English (US)",
    "tr-TR": "Turkish",
}
DEFAULT_LANGUAGE = "en-US"
# Stop waiting for Azure after this many seconds, so a request can never hang forever.
RECOGNITION_TIMEOUT_SECONDS = 120


class SpeechConfigError(Exception):
    """Raised when the Azure key or region is missing from .env."""


class SpeechServiceError(Exception):
    """Raised when Azure could not complete the request."""


class NoSpeechError(Exception):
    """Raised when the audio was valid but contained no recognizable speech."""


def _speech_config():
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    if not key or not region:
        raise SpeechConfigError("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in Week-5-Task-1/.env.")
    return speechsdk.SpeechConfig(subscription=key, region=region)


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
    if language not in LANGUAGES:
        raise ValueError(f"Unknown language '{language}'.")
    if not wav_bytes:
        raise ValueError("Please record or choose an audio file.")

    config = _speech_config()
    # The SDK reads audio from a file path, so write the upload to a temporary file.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
        temp.write(wav_bytes)
        temp_path = Path(temp.name)
    try:
        _check_wav(temp_path)
        audio_config = speechsdk.audio.AudioConfig(filename=str(temp_path))
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=config, audio_config=audio_config, language=language
        )

        phrases = []
        errors = []
        done = threading.Event()

        def on_recognized(event):
            if event.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                phrases.append(event.result.text)

        def on_canceled(event):
            # EndOfStream is the normal end of a file; only Error is a real failure.
            if event.reason == speechsdk.CancellationReason.Error:
                errors.append(event.error_details)
            done.set()

        recognizer.recognized.connect(on_recognized)
        recognizer.canceled.connect(on_canceled)
        recognizer.session_stopped.connect(lambda event: done.set())

        recognizer.start_continuous_recognition()
        finished = done.wait(RECOGNITION_TIMEOUT_SECONDS)
        recognizer.stop_continuous_recognition()
        # Release the SDK's handle on the file before deleting it.
        del recognizer, audio_config
    finally:
        temp_path.unlink(missing_ok=True)

    if errors:
        raise SpeechServiceError(f"Azure could not transcribe the audio: {errors[0]}")
    if not finished:
        raise SpeechServiceError("Azure took too long to transcribe the audio.")
    text = " ".join(phrases).strip()
    if not text:
        raise NoSpeechError("No speech could be recognized in the audio.")
    return text
