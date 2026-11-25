# Week 9: Transformers, what can they do?

| Folder | Contents |
|---|---|
| [`task-1/`](task-1/) | The ten in-class tasks, one script each |
| [`task-3/`](task-3/) | The same ten tasks as an object-oriented module, with a Gradio demo |
| [`task-4/`](task-4/) | Tokenizer and model basics from chapter 2: load & save, encode & decode, padding, truncation, special tokens |

`pipelines_demo.py` holds the examples from the [Hugging Face LLM course, chapter 1.3](https://huggingface.co/learn/llm-course/chapter1/3),
with every model downloaded in advance, so they run without internet.

## Setup

```bash
cd Week-9
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python download_models.py      # about 10 GB, into ~/.cache/huggingface/hub
```

## Run

```bash
.venv/bin/python pipelines_demo.py                # all 11 examples
.venv/bin/python pipelines_demo.py translation    # just one
HF_HUB_OFFLINE=1 .venv/bin/python pipelines_demo.py   # check that everything works offline
```

## The examples and their models

| Example | `pipeline()` task | Model | Result |
|---|---|---|---|
| `sentiment` | sentiment-analysis | distilbert-base-uncased-finetuned-sst-2-english (default) | POSITIVE 0.96, NEGATIVE 1.00 |
| `zero-shot` | zero-shot-classification | facebook/bart-large-mnli (default) | education 0.84 |
| `generation` | text-generation | openai-community/gpt2 (default) | continues the sentence |
| `smollm` | text-generation | **HuggingFaceTB/SmolLM2-360M** | continues the sentence, two versions |
| `fill-mask` | fill-mask | distilroberta-base (default) | "mathematical", "computational" |
| `ner` | ner | bert-large-cased-finetuned-conll03-english (default) | Sylvain = person, Hugging Face = organization, Brooklyn = location |
| `qa` | question-answering | distilbert-base-cased-distilled-squad (default) | "Hugging Face" |
| `summarization` | summarization | sshleifer/distilbart-cnn-12-6 (default) | a 3-sentence summary |
| `translation` | translation | **Helsinki-NLP/opus-mt-fr-en** | "This course is produced by Hugging Face." |
| `image` | image-classification | **google/vit-base-patch16-224** | lynx 0.43 (the sample is a big fluffy cat) |
| `speech` | automatic-speech-recognition | **openai/whisper-large-v3** | "I have a dream that one day this nation will rise up..." |

The four models in bold are the ones named in the assignment. `download_models.py`
also fetches Helsinki-NLP/opus-mt-tc-big-en-tr (English to Turkish). The others are the models
`pipeline()` picks when no model is given; `download_models.py` fetches them at the exact
revision transformers 4.57 asks for, so the cache is used instead of downloading again.

Only one copy of each model's weights is downloaded. Whisper's repository is 24.7 GB because it
holds the same model in several formats; the safetensors copy alone is 3.1 GB.

## Files

| File | Role |
|---|---|
| `download_models.py` | Downloads the 12 models into the Hugging Face cache. |
| `pipelines_demo.py` | The 11 examples from the course page. |
| `samples/` | The course page's sample image and audio clip. |
