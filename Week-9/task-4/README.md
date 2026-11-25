# Week 9, Task 4: Tokenizers and models

Five short scripts on what happens behind `pipeline()`, from the
[Hugging Face LLM course, chapter 2](https://huggingface.co/learn/llm-course/chapter2/1).
They all use the model of the course's "Behind the pipeline" section,
`distilbert/distilbert-base-uncased-finetuned-sst-2-english` (the sentiment-analysis default),
which `download_models.py` already put in the cache, so they run without internet.

## Run

From the `Week-9` folder:

```bash
.venv/bin/python task-4/load_and_save.py
.venv/bin/python task-4/encode_decode.py
.venv/bin/python task-4/padding.py
.venv/bin/python task-4/truncation.py
.venv/bin/python task-4/special_tokens.py
```

## The tasks

| Script | Video | What it shows | Result |
|---|---|---|---|
| `load_and_save.py` | `Task4_load_and_save.avi` | `from_pretrained()` loads the tokenizer and model, `save_pretrained()` writes them to `saved_model/`, and `from_pretrained("saved_model")` loads them back | Both copies say POSITIVE (0.9598) for the same sentence |
| `encode_decode.py` | `Task4_encode_decode.avi` | `tokenize()` splits text into tokens, `convert_tokens_to_ids()` turns them into numbers, `decode()` turns the numbers back into text | "Transformer" becomes `transform` + `##er`; decoding gives the sentence back in lower case |
| `padding.py` | `Task4_padding.avi` | Sentences of 8 and 16 tokens are padded to 16 with `[PAD]`, and the attention mask marks the padding with 0 | With the mask the short sentence gives the same logits alone and padded (4.1692, -3.3464 → NEGATIVE 0.9995); without it they change (3.4603, -2.9194 → NEGATIVE 0.9983) |
| `truncation.py` | `Task4_truncation.avi` | `truncation=True, max_length=8` cuts a 16-token sentence to 8 | `[CLS] i've been waiting for [SEP]`: the limit counts `[CLS]` and `[SEP]`, which are kept |
| `special_tokens.py` | `Task4_special_tokens.avi` | The tokenizer adds `[CLS]` and `[SEP]` by itself (`add_special_tokens=False` turns that off); then a new token of our own is added | "EE471" was split into `ee`, `##47`, `##1`; after `add_special_tokens()` it is one token, id 30522, and the model gets a new embedding for it with `resize_token_embeddings()` |

## Notes

- The model is "uncased": the tokenizer lower-cases the text, which is why the decoded sentences
  are in lower case. The added token `EE471` keeps its capitals because special tokens are never
  changed.
- `saved_model/` is 268 MB, so it is in `.gitignore`; `load_and_save.py` creates it again.
- `common.py` turns on offline mode and hides library warnings so the output is easy to read in
  the videos.
