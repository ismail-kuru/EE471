"""Text Classifier: sorts text into categories; this model tells if a review is positive or negative.

Usage: python text_classifier.py ["some text"]   (default: a few example reviews)
Model: a BERT classifier trained on movie reviews (SST-2), with the classes "positive" and "negative".
"""

import sys

from mediapipe.tasks.python import BaseOptions, text

from common import model

reviews = sys.argv[1:] or [
    "This movie was wonderful, I loved every minute of it.",
    "The plot was boring and the acting was terrible.",
    "It was okay, nothing special.",
]

options = text.TextClassifierOptions(base_options=BaseOptions(model_asset_path=model("bert_classifier.tflite")))
with text.TextClassifier.create_from_options(options) as classifier:
    for review in reviews:
        categories = classifier.classify(review).classifications[0].categories
        best = max(categories, key=lambda c: c.score)
        print(f"{review!r}: {best.category_name} ({best.score:.0%})")
