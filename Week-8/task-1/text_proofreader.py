"""Text Proofreader: fixes spelling and grammar mistakes in a text.

Usage: python text_proofreader.py ["text with mistakes"]   (default: example sentences)
Model: a 200M-parameter Gemma-based model that runs on the computer. Besides the corrected text it
returns the changes as a list of kept, inserted and deleted pieces.
"""

import sys

from mediapipe.tasks.python import BaseOptions, text

from common import model

sentences = sys.argv[1:] or [
    "Their are severel typos in this sentance.",
    "Yesterday I go to the univercity and meet my freinds.",
    "MediaPipe run on many devise and it are very fast.",
]

options = text.TextProofreaderOptions(base_options=BaseOptions(model_asset_path=model("proofread_quant_200m.litertlm")))
with text.TextProofreader.create_from_options(options) as proofreader:
    for sentence in sentences:
        result = proofreader.proofread(sentence)
        print(f"before: {sentence}")
        print(f"after:  {result.proofread_text}\n")
