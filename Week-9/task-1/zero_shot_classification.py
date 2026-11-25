"""Task 1.2: zero-shot classification, choosing labels the model was never trained on."""

from common import show, title
from transformers import pipeline

SENTENCE = "Berkshire keeps their cash reserves at an extremely high level."
LABELS = ["finance", "education", "politics", "sports", "technology"]

classifier = pipeline("zero-shot-classification")  # default: facebook/bart-large-mnli
result = classifier(SENTENCE, candidate_labels=LABELS)

title("Zero-shot classification")
show("Sentence", SENTENCE)
for label, score in zip(result["labels"], result["scores"]):
    show(label, f"{score:.4f}")
