"""Task 4.1: load a model and its tokenizer, save them to a folder, and load them back from it."""

import torch
from common import CHECKPOINT, HERE, REVISION, show, title
from transformers import AutoModelForSequenceClassification, AutoTokenizer

SAVE_DIR = HERE / "saved_model"
SENTENCE = "I've been waiting for a HuggingFace course my whole life."

# 1) Load from the Hugging Face Hub (here: from the local cache of the Hub).
tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, revision=REVISION)
model = AutoModelForSequenceClassification.from_pretrained(CHECKPOINT, revision=REVISION)

# 2) Save both into a folder of our own.
tokenizer.save_pretrained(SAVE_DIR)
model.save_pretrained(SAVE_DIR)

# 3) Load them back from that folder, as if it were a model on the Hub.
tokenizer2 = AutoTokenizer.from_pretrained(SAVE_DIR)
model2 = AutoModelForSequenceClassification.from_pretrained(SAVE_DIR)


def predict(tokenizer, model):
    inputs = tokenizer(SENTENCE, return_tensors="pt")
    with torch.no_grad():
        probabilities = model(**inputs).logits.softmax(dim=-1)[0]
    best = int(probabilities.argmax())
    return f"{model.config.id2label[best]} ({probabilities[best]:.4f})"


title("Load & save a model")
show("Loaded", f"{CHECKPOINT} ({model.num_parameters():,} parameters)")
show("Saved to", SAVE_DIR.name + "/")
for file in sorted(SAVE_DIR.iterdir()):
    show("", f"{file.name:<24} {file.stat().st_size / 1e6:8.2f} MB")
print()
show("Sentence", SENTENCE)
show("Original model", predict(tokenizer, model))
show("Reloaded model", predict(tokenizer2, model2))
