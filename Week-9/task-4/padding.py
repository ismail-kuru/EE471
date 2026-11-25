"""Task 4.3: pad sentences of different lengths so they fit in one batch (a rectangular tensor)."""

import torch
from common import CHECKPOINT, REVISION, show, title
from transformers import AutoModelForSequenceClassification, AutoTokenizer

SENTENCES = ["I hate this so much!", "I've been waiting for a HuggingFace course my whole life."]

tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, revision=REVISION)
model = AutoModelForSequenceClassification.from_pretrained(CHECKPOINT, revision=REVISION)

title("Input padding")
show("Pad token", f"{tokenizer.pad_token} (id {tokenizer.pad_token_id})")
show("Not padded", [len(ids) for ids in tokenizer(SENTENCES)["input_ids"]])

# padding=True pads every sentence to the longest one; the attention mask marks the padding with 0
# so the model ignores it.
batch = tokenizer(SENTENCES, padding=True, return_tensors="pt")
for name, row, mask in zip(["Short", "Long"], batch["input_ids"], batch["attention_mask"]):
    print()
    show(name, tokenizer.convert_ids_to_tokens(row))
    show("attention_mask", mask.tolist())

# The short sentence gives the same result alone and padded, as long as the attention mask is used.
with torch.no_grad():
    alone = model(**tokenizer(SENTENCES[0], return_tensors="pt")).logits[0]
    padded = model(**batch).logits[0]
    no_mask = model(input_ids=batch["input_ids"]).logits[0]


def verdict(logits):
    """The logits, then the label with the highest score and its probability (softmax of the logits)."""
    probabilities = logits.softmax(dim=-1)
    best = int(probabilities.argmax())
    return f"{[round(x, 4) for x in logits.tolist()]}  ->  {model.config.id2label[best]} ({probabilities[best]:.4f})"


print()
show("Logits alone", verdict(alone))
show("Padded + mask", verdict(padded))
show("Padded, no mask", verdict(no_mask))
