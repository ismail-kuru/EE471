import os
from pathlib import Path
from threading import Event
import wave
from xml.sax.saxutils import escape

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / ".env"
DEFAULT_VOICE = "tr-TR-AhmetNeural"
DEFAULT_RECOGNITION_LANGUAGE = "tr-TR"


def get_speech_credentials() -> tuple[str, str]:
    load_dotenv(dotenv_path=DOTENV_PATH)

    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")

    if not speech_key or not speech_region:
        raise RuntimeError("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in your .env file.")

    return speech_key, speech_region


def get_default_voice() -> str:
    load_dotenv(dotenv_path=DOTENV_PATH)
    return os.getenv("AZURE_SPEECH_VOICE", DEFAULT_VOICE)


def get_default_recognition_language() -> str:
    load_dotenv(dotenv_path=DOTENV_PATH)
    return os.getenv("AZURE_SPEECH_RECOGNITION_LANGUAGE", DEFAULT_RECOGNITION_LANGUAGE)


def format_percentage(multiplier: float) -> str:
    percentage = round((multiplier - 1.0) * 100)
    return f"{percentage:+d}%"


def build_ssml_preview(text: str, voice_name: str, speed: float, pitch: float) -> str:
    escaped_text = escape(text or "")
    rate = format_percentage(speed)
    pitch_value = format_percentage(pitch)
    return (
        "<speak version=\"1.0\" xml:lang=\"en-US\">"
        f"<voice name=\"{voice_name}\">"
        f"<prosody rate=\"{rate}\" pitch=\"{pitch_value}\">{escaped_text}</prosody>"
        "</voice>"
        "</speak>"
    )


def get_wav_duration_seconds(audio_path: Path) -> float:
    with wave.open(str(audio_path), "rb") as wav_file:
        frame_rate = wav_file.getframerate()
        frame_count = wav_file.getnframes()

    if frame_rate <= 0:
        return 0.0

    return frame_count / frame_rate


def synthesize_text_to_file(
    text: str,
    output_path: Path,
    voice_name: str = DEFAULT_VOICE,
    speed: float = 1.0,
    pitch: float = 1.0,
) -> Path:
    speech_key, speech_region = get_speech_credentials()
    selected_voice = voice_name or get_default_voice()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_synthesis_voice_name = selected_voice
    audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )
    ssml = build_ssml_preview(text=text, voice_name=selected_voice, speed=speed, pitch=pitch)

    result = synthesizer.speak_ssml_async(ssml).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return output_path

    cancellation = result.cancellation_details
    details = cancellation.error_details or "Unknown Azure Speech error."
    raise RuntimeError(f"Synthesis failed: {details}")


def transcribe_audio_file(audio_path: Path, recognition_language: str | None = None) -> str:
    speech_key, speech_region = get_speech_credentials()
    selected_language = recognition_language or get_default_recognition_language()

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_recognition_language = selected_language
    audio_config = speechsdk.audio.AudioConfig(filename=str(audio_path))
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )
    chunks: list[str] = []
    errors: list[str] = []
    done = Event()

    def on_recognized(evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
            chunks.append(evt.result.text.strip())

    def on_canceled(evt: speechsdk.SpeechRecognitionCanceledEventArgs) -> None:
        if evt.reason == speechsdk.CancellationReason.Error:
            errors.append(evt.error_details or "Unknown Azure Speech error.")
        done.set()

    def on_session_stopped(evt: speechsdk.SessionEventArgs) -> None:
        done.set()

    recognizer.recognized.connect(on_recognized)
    recognizer.canceled.connect(on_canceled)
    recognizer.session_stopped.connect(on_session_stopped)

    wait_timeout = max(10.0, min(get_wav_duration_seconds(audio_path) + 5.0, 60.0))

    recognizer.start_continuous_recognition_async().get()
    done.wait(timeout=wait_timeout)
    recognizer.stop_continuous_recognition_async().get()

    if errors:
        raise RuntimeError(f"Transcription failed: {' | '.join(errors)}")

    transcript = " ".join(chunk for chunk in chunks if chunk).strip()
    if transcript:
        return transcript

    raise RuntimeError("No speech could be recognized from the provided audio.")
