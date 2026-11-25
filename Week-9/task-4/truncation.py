"""Task 4.4: cut sentences that are longer than a limit (truncation)."""

from common import CHECKPOINT, REVISION, show, title
from transformers import AutoTokenizer

SENTENCE = "I've been waiting for a HuggingFace course my whole life."
MAX_LENGTH = 8

tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, revision=REVISION)
full = tokenizer(SENTENCE)
cut = tokenizer(SENTENCE, truncation=True, max_length=MAX_LENGTH)  # [CLS] and [SEP] count too

title("Input truncation")
show("Model limit", f"{tokenizer.model_max_length} tokens")
show("Full", f"{len(full['input_ids'])} tokens  {tokenizer.convert_ids_to_tokens(full['input_ids'])}")
show(f"max_length={MAX_LENGTH}", f"{len(cut['input_ids'])} tokens  {tokenizer.convert_ids_to_tokens(cut['input_ids'])}")
show("Decoded", tokenizer.decode(cut["input_ids"]))
