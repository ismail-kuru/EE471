"""Task 1.5: find the person, the organization they work for and where they live."""

from common import show, title
from transformers import pipeline

SENTENCE = ("I am Nate, a research assistant at Izmir Institute of Technology, and currently living "
            "and working in the beautiful city İzmir in Türkiye.")


def extract(sentence=SENTENCE):
    recognizer = pipeline("ner", aggregation_strategy="simple")  # default: bert-large-cased-finetuned-conll03-english
    entities = recognizer(sentence)
    first = {}
    for entity in entities:
        first.setdefault(entity["entity_group"], entity["word"])
    return entities, {"person": first.get("PER"), "organization": first.get("ORG"), "city": first.get("LOC")}


if __name__ == "__main__":
    entities, found = extract()
    title("Named entity recognition")
    show("Sentence", SENTENCE)
    print()
    for entity in entities:
        show(entity["entity_group"], f"{entity['word']} ({entity['score']:.4f})")
    print()
    for key, value in found.items():
        show(key, value)
