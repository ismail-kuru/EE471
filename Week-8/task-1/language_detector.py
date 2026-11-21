"""Language Detector: tells which language a piece of text is written in.

Usage: python language_detector.py ["some text"]   (default: a few example sentences)
Model: a small classifier that knows 110 languages and returns ISO codes such as "en" or "tr".
"""

import sys

from mediapipe.tasks.python import BaseOptions, text

from common import model

sentences = sys.argv[1:] or [
    "MediaPipe makes on-device machine learning easy.",
    "Bugün hava çok güzel, dışarı çıkalım.",
    "Je voudrais un café, s'il vous plaît.",
    "Wie spät ist es?",
]

options = text.LanguageDetectorOptions(base_options=BaseOptions(model_asset_path=model("language_detector.tflite")), max_results=2)
with text.LanguageDetector.create_from_options(options) as detector:
    for sentence in sentences:
        result = detector.detect(sentence)
        guesses = ", ".join(f"{d.language_code} {d.probability:.0%}" for d in result.detections)
        print(f"{sentence!r}: {guesses}")
