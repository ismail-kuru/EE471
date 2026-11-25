"""Task 1.1: sentiment analysis of two sentences."""

from common import show, title
from transformers import pipeline

SENTENCES = [
    "I've been waiting for a modern software practices course my whole life.",
    "I hate software courses",
]

classifier = pipeline("sentiment-analysis")  # default: distilbert-base-uncased-finetuned-sst-2-english

title("Sentiment analysis")
for sentence, result in zip(SENTENCES, classifier(SENTENCES)):
    show("Sentence", sentence)
    show("Result", f"{result['label']} ({result['score']:.4f})\n")
