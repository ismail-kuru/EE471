"""Text-to-Speech: turns text into spoken audio, on the computer, without an internet service.

Usage: python text_to_speech.py ["text to say"]   (default: an example sentence)
Model: Phonon 31M, a small English voice model. The result is 24 kHz audio; this script saves it
as outputs/text_to_speech.wav, which audio_transcriber.py can turn back into text.
"""

import sys
import wave

import numpy as np
from mediapipe.tasks.python import BaseOptions, audio

from common import OUTPUTS, model

text = " ".join(sys.argv[1:]) or "Hello! This sentence was spoken by MediaPipe text to speech, running on my own computer."

options = audio.TextToSpeechOptions(base_options=BaseOptions(model_asset_path=model("phonon_int8.litertlm")))
with audio.TextToSpeech.create_from_options(options) as tts:
    print("Voices:", ", ".join(f"{v.voice_id} ({v.locale})" for v in tts.list_voices()))
    result = tts.synthesize(text)

# The model returns numbers between -1 and 1; a WAV file stores them as 16-bit integers.
samples = np.asarray(result.samples, dtype=np.float32)
OUTPUTS.mkdir(exist_ok=True)
out = OUTPUTS / "text_to_speech.wav"
with wave.open(str(out), "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(result.sample_rate_hz)
    wav.writeframes((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())

print(f"Text: {text!r}")
print(f"Saved {out.relative_to(OUTPUTS.parent)}: {len(samples) / result.sample_rate_hz:.1f} s at {result.sample_rate_hz} Hz")
