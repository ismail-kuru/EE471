"""Azure Speech helpers. Credentials come from the .env file next to this script."""

import os
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# Voices offered on the page; the API only accepts these.
VOICES = {
    "en-US-JennyNeural": "English (US) – Jenny",
    "en-US-GuyNeural": "English (US) – Guy",
    "tr-TR-EmelNeural": "Turkish – Emel",
    "tr-TR-AhmetNeural": "Turkish – Ahmet",
}
DEFAULT_VOICE = "en-US-JennyNeural"
MAX_TEXT_LENGTH = 1000


class SpeechConfigError(Exception):
    """Raised when the Azure key or region is missing from .env."""


class SpeechServiceError(Exception):
    """Raised when Azure could not complete the request."""


def _speech_config():
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    if not key or not region:
        raise SpeechConfigError("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in Week-5-Task-1/.env.")
    return speechsdk.SpeechConfig(subscription=key, region=region)


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
