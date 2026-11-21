"""Audio Classifier: tells what kind of sound is in an audio file (speech, music, dog bark...).

Usage: python audio_classifier.py [file.wav]   (default: samples/speech.wav, also try samples/tone.wav)
Model: YAMNet, which knows 521 sound classes. The audio is cut into ~1 second pieces and
each piece gets its own result.
"""

import wave

import numpy as np
from mediapipe.tasks.python import BaseOptions, audio
from mediapipe.tasks.python.components.containers import AudioData

from common import input_path, model

path = input_path("speech.wav")

# Read the WAV file as numbers between -1 and 1, which is what MediaPipe expects.
with wave.open(str(path)) as wav:
    sample_rate = wav.getframerate()
    samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
    if wav.getnchannels() == 2:
        samples = samples.reshape(-1, 2).mean(axis=1)
audio_data = AudioData.create_from_array(samples.astype(np.float32) / 32768, sample_rate)

options = audio.AudioClassifierOptions(base_options=BaseOptions(model_asset_path=model("yamnet.tflite")), max_results=3)
with audio.AudioClassifier.create_from_options(options) as classifier:
    results = classifier.classify(audio_data)  # One result per piece of audio.

print(f"{path.name}: {len(samples) / sample_rate:.1f} s at {sample_rate} Hz")
for result in results:
    top = result.classifications[0].categories
    labels = ", ".join(f"{c.category_name} {c.score:.0%}" for c in top)
    print(f"  {result.timestamp_ms / 1000:4.1f} s: {labels}")
