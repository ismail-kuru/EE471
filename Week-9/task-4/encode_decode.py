"""Task 4.2: turn text into token ids (encoding) and ids back into text (decoding)."""

from common import CHECKPOINT, REVISION, show, title
from transformers import AutoTokenizer

SENTENCE = "Using a Transformer network is simple"

tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, revision=REVISION)

# Encoding, step by step: text -> tokens -> ids.
tokens = tokenizer.tokenize(SENTENCE)
ids = tokenizer.convert_tokens_to_ids(tokens)

# Decoding: ids -> text.
text = tokenizer.decode(ids)

title("Text encoding and decoding")
show("Text", SENTENCE)
show("Tokens", tokens)
show("Ids", ids)
show("Decoded", text)
