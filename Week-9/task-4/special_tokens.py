"""Task 4.5: special tokens, the ones the tokenizer adds by itself and new ones of our own."""

from common import CHECKPOINT, REVISION, show, title
from transformers import AutoModelForSequenceClassification, AutoTokenizer

SENTENCE = "I love the EE471 course."

tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, revision=REVISION)
model = AutoModelForSequenceClassification.from_pretrained(CHECKPOINT, revision=REVISION)

title("Adding special tokens")

# 1) Calling the tokenizer adds [CLS] at the start and [SEP] at the end, as the model was trained.
with_special = tokenizer(SENTENCE)["input_ids"]
without = tokenizer(SENTENCE, add_special_tokens=False)["input_ids"]
show("Special tokens", f"{tokenizer.all_special_tokens}")
show("With", tokenizer.decode(with_special))
show("Without", tokenizer.decode(without))

# 2) A token of our own: before, the word is split into pieces; after, it is a single token.
print()
show("Before", tokenizer.tokenize(SENTENCE))
added = tokenizer.add_special_tokens({"additional_special_tokens": ["EE471"]})
model.resize_token_embeddings(len(tokenizer))  # the model needs a vector for each new token
show("After", tokenizer.tokenize(SENTENCE))
show("New token", f"EE471 -> id {tokenizer.convert_tokens_to_ids('EE471')} ({added} added, vocabulary {len(tokenizer)})")
