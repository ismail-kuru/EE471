"""Task 1.4: fill the gap in a sentence with the most likely words."""

from common import show, title
from transformers import pipeline

unmasker = pipeline("fill-mask")  # default: distilroberta-base, whose gap token is <mask>

results = unmasker("To understand generative AI, one must study <mask> well.", top_k=3)
for result in results:
    print(result)
