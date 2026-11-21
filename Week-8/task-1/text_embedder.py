"""Text Embedder: turns text into a list of numbers (an embedding) so texts can be compared by meaning.

Usage: python text_embedder.py ["first text" "second text" ...]   (default: example sentences)
Model: Universal Sentence Encoder. Sentences with similar meaning get similar vectors, which
the cosine similarity measures: close to 1 = same meaning, close to 0 = unrelated.
"""

import sys
from itertools import combinations

from mediapipe.tasks.python import BaseOptions, text

from common import model

sentences = sys.argv[1:] or [
    "I love playing football with my friends.",
    "Soccer with friends is my favorite thing.",
    "The stock market fell sharply today.",
]

options = text.TextEmbedderOptions(base_options=BaseOptions(model_asset_path=model("universal_sentence_encoder.tflite")))
with text.TextEmbedder.create_from_options(options) as embedder:
    embeddings = [embedder.embed(s).embeddings[0] for s in sentences]

print(f"Each sentence becomes {len(embeddings[0].embedding)} numbers.")
for (i, a), (j, b) in combinations(enumerate(embeddings), 2):
    similarity = text.TextEmbedder.cosine_similarity(a, b)
    print(f"{similarity:.2f}  {sentences[i]!r} vs {sentences[j]!r}")
