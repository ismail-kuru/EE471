"""Task 1.10: transcribe speech with OpenAI's Whisper. Usage: python speech_recognition.py [audio file]"""

import textwrap

import torch
from common import input_path, show, title
from transformers import pipeline

audio = input_path("mlk.flac")
# The downloaded weights are float16, which gives garbage ("!") on the Mac GPU (MPS); float32 works.
transcriber = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3", dtype=torch.float32)
text = transcriber(str(audio))["text"].strip()

title("Automatic speech recognition (openai/whisper-large-v3)")
show("Audio", audio.name)
print(textwrap.fill(f"        Text: {text}", 100))
