"""Azure Speech helpers for the voice calculator. Credentials come from .env."""

import functools
import os
import tempfile
import threading
import wave
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

import commands

load_dotenv(Path(__file__).resolve().parent / ".env")

VOICE = "en-US-JennyNeural"
LANGUAGE = "en-US"
MAX_SPEAK_LENGTH = 100
# Stop waiting for Azure after this many seconds, so a request can never hang forever.
RECOGNITION_TIMEOUT_SECONDS = 30


class SpeechConfigError(Exception):
    """Raised when the Azure key or region is missing from .env."""


class SpeechServiceError(Exception):
    """Raised when Azure could not complete the request."""


class NoSpeechError(Exception):
    """Raised when the audio contained no recognizable speech."""


def _speech_config():
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    if not key or not region:
        raise SpeechConfigError("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in Week-5-Task-2/.env.")
    return speechsdk.SpeechConfig(subscription=key, region=region)


# --- The calculator speaks ---

def speak(text):
    """Return WAV bytes of text read aloud.

    Raises:
        ValueError: If the text is empty or too long.
        SpeechConfigError, SpeechServiceError: If Azure cannot be used.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Nothing to say.")
    if len(text) > MAX_SPEAK_LENGTH:
        raise ValueError(f"Text is too long (max {MAX_SPEAK_LENGTH} characters).")
    return _synthesize(text.strip())


# The keys say the same few words again and again, so keep the audio instead of
# asking Azure every time. Failures raise, so they are never cached.
@functools.lru_cache(maxsize=256)
def _synthesize(text):
    config = _speech_config()
    config.speech_synthesis_voice_name = VOICE
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    )
    # audio_config=None keeps the audio in memory instead of playing it on the server's speakers.
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    details = result.cancellation_details
    raise SpeechServiceError(f"Azure could not speak the text: {details.error_details or details.reason}")


# --- The calculator listens ---

def _check_wav(path):
    """Raise ValueError unless the file is a 16-bit PCM WAV that Azure can read."""
    try:
        with wave.open(str(path), "rb") as wav:
            if wav.getsampwidth() != 2 or wav.getnframes() == 0:
                raise ValueError("Audio must be a non-empty 16-bit PCM WAV file.")
    except (wave.Error, EOFError):
        raise ValueError("Audio must be a WAV file.")


def listen(wav_bytes):
    """Recognize a spoken command such as "five plus two is" and return the text.

    Continuous recognition is used so pauses between the words ("five … plus
    … two … is") do not cut the command short.

    Raises:
        ValueError: If the audio is not a usable WAV file.
        SpeechConfigError, SpeechServiceError: If Azure cannot be used.
        NoSpeechError: If nothing was recognized.
    """
    if not wav_bytes:
        raise ValueError("No audio was recorded.")
    config = _speech_config()

    # The SDK reads audio from a file path, so write the upload to a temporary file.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
        temp.write(wav_bytes)
        path = Path(temp.name)
    try:
        _check_wav(path)
        audio_config = speechsdk.audio.AudioConfig(filename=str(path))
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=config, audio_config=audio_config, language=LANGUAGE
        )
        # Tell Azure which words to expect, so short commands such as "two" or "is"
        # are not heard as "to" or dropped.
        phrases = speechsdk.PhraseListGrammar.from_recognizer(recognizer)
        for word in commands.KEY_WORDS.values():
            phrases.addPhrase(word)

        heard, errors = [], []
        done = threading.Event()

        def on_recognized(event):
            if event.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                heard.append(event.result.text)

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
        del recognizer, audio_config, phrases
    finally:
        path.unlink(missing_ok=True)

    if errors:
        raise SpeechServiceError(f"Azure could not recognize the audio: {errors[0]}")
    if not finished:
        raise SpeechServiceError("Azure took too long to recognize the audio.")
    text = " ".join(heard).strip()
    if not text:
        raise NoSpeechError("I didn't hear anything. Try again a bit louder.")
    return text
