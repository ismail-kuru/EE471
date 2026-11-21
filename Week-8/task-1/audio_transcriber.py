"""Audio Transcriber: turns speech in an audio file into written text (speech-to-text).

Usage: python audio_transcriber.py [file.wav]   (default: samples/speech.wav;
       also try outputs/text_to_speech.wav after running text_to_speech.py)
Model: NVIDIA Parakeet TDT 0.6B, which understands 25 European languages and adds punctuation
and capital letters. It runs on the computer, without an internet service.
"""

import wave

import numpy as np
from mediapipe.tasks.python import BaseOptions, audio

from common import input_path, model

path = input_path("speech.wav")

# Read the WAV file as mono numbers between -1 and 1, which is what the transcriber expects.
with wave.open(str(path)) as wav:
    sample_rate = wav.getframerate()
    samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if wav.getnchannels() == 2:
        samples = samples.reshape(-1, 2).mean(axis=1)

options = audio.AudioTranscriberOptions(
    base_options=BaseOptions(model_asset_path=model("parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm")),
    sample_rate_hz=sample_rate,  # Other rates than 16 kHz are converted automatically.
)
with audio.AudioTranscriber.create_from_options(options) as transcriber:
    result = transcriber.transcribe(samples, end_of_stream=True)  # The whole file in one call.

print(f"{path.name}: {len(samples) / sample_rate:.1f} s of audio")
print(f"Text: {result.text}")
for segment in result.segments:
    print(f"  {segment.from_timestamp_ms / 1000:4.1f}-{segment.to_timestamp_ms / 1000:4.1f} s: {segment.transcript}")
