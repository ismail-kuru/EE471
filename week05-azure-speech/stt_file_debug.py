from pathlib import Path
from threading import Event
import sys

import azure.cognitiveservices.speech as speechsdk

from speech_service import get_speech_credentials, get_wav_duration_seconds


def run_recognize_once(audio_path: Path, language: str) -> None:
    speech_key, speech_region = get_speech_credentials()
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_recognition_language = language
    audio_config = speechsdk.audio.AudioConfig(filename=str(audio_path))
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )

    print("=== recognize_once ===")
    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(result.text)
        return

    if result.reason == speechsdk.ResultReason.NoMatch:
        print(f"No speech could be recognized: {result.no_match_details}")
        return

    cancellation = result.cancellation_details
    print(f"Canceled: {cancellation.reason}")
    if cancellation.reason == speechsdk.CancellationReason.Error:
        print(f"Error details: {cancellation.error_details}")


def run_continuous_recognition(audio_path: Path, language: str) -> None:
    speech_key, speech_region = get_speech_credentials()
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_recognition_language = language
    audio_config = speechsdk.audio.AudioConfig(filename=str(audio_path))
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )

    done = Event()
    chunks: list[str] = []
    errors: list[str] = []

    def on_recognized(evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
            chunks.append(evt.result.text)
            print(f"chunk: {evt.result.text}")

    def on_canceled(evt: speechsdk.SpeechRecognitionCanceledEventArgs) -> None:
        errors.append(f"{evt.reason}: {evt.error_details}")
        done.set()

    def on_session_stopped(evt: speechsdk.SessionEventArgs) -> None:
        done.set()

    recognizer.recognized.connect(on_recognized)
    recognizer.canceled.connect(on_canceled)
    recognizer.session_stopped.connect(on_session_stopped)

    wait_timeout = max(10.0, min(get_wav_duration_seconds(audio_path) + 5.0, 60.0))

    print("\n=== continuous_recognition ===")
    print(f"waiting up to {wait_timeout:.1f} seconds for the full file...")
    recognizer.start_continuous_recognition_async().get()
    done.wait(timeout=wait_timeout)
    recognizer.stop_continuous_recognition_async().get()

    if errors:
        print("canceled:")
        for error in errors:
            print(error)

    print("\njoined:")
    print(" ".join(chunks))


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python stt_file_debug.py <wav-path> [language]")
        return 1

    audio_path = Path(sys.argv[1]).expanduser().resolve()
    language = sys.argv[2] if len(sys.argv) > 2 else "en-US"

    if not audio_path.exists():
        print(f"File not found: {audio_path}")
        return 1

    run_recognize_once(audio_path, language)
    run_continuous_recognition(audio_path, language)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
