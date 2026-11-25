# Week 9, Task 3: an object-oriented module and a Gradio demo

The ten tasks of Task 1 as one Python module, and a web demo with a tab for each task.

## Run

From the `Week-9` folder, after `download_models.py` and `pip install -r requirements.txt`:

```bash
cd task-3
../.venv/bin/python app.py                  # then open http://127.0.0.1:7860
../.venv/bin/python transformer_tasks.py    # the module alone: every task on the Task 1 inputs
```

A model is loaded the first time its tab's **Submit** is pressed, so the first answer in each tab
takes a few seconds longer (Whisper about 15 s). Each tab has the Task 1 input as an example
below it; click the example, then Submit.

## Files

| File | Role |
|---|---|
| `transformer_tasks.py` | The module: a `Task` base class, one subclass per task and `TransformerTasks`, which holds all ten. |
| `app.py` | The Gradio demo: one `gr.Interface` per task, put together with `gr.TabbedInterface`. |
| `examples.py` | The Task 1 inputs, used by both files above. |

## The module

```python
from transformer_tasks import TransformerTasks

tasks = TransformerTasks()
tasks.sentiment.run("I hate software courses")              # {'NEGATIVE': 0.89, 'POSITIVE': 0.11}
tasks.qa.run("Where do I work?", "... at Izmir Institute of Technology ...")
tasks.image.run("cat.jpg", top_k=3)
```

- **`Task`** holds what every task shares: the `pipeline()` task name, the model and the pipeline
  itself. The `pipeline` property creates it on first use and then keeps it, so unused tasks never
  load a model and used ones load it only once.
- **The ten subclasses** (`SentimentAnalysis`, `ZeroShotClassification`, `TextGeneration`,
  `FillMask`, `NamedEntityRecognition`, `QuestionAnswering`, `Summarization`, `Translation`,
  `ImageClassification`, `SpeechRecognition`) only set their task and model and write `run()`,
  which turns the pipeline's raw output into a simple result.
- **`TransformerTasks`** creates one object of each, so the app needs a single import.

| Attribute | Task | Model |
|---|---|---|
| `sentiment` | Sentiment analysis | distilbert-base-uncased-finetuned-sst-2-english |
| `zero_shot` | Zero-shot classification | facebook/bart-large-mnli |
| `generation` | Text generation, two completions of at most N words | HuggingFaceTB/SmolLM2-360M |
| `fill_mask` | Mask filling; the gap can be written `[…]`, `[MASK]` or `<mask>` | distilroberta-base |
| `ner` | Named entity recognition, plus `summary()` for the person, organization and location | bert-large-cased-finetuned-conll03-english |
| `qa` | Question answering | distilbert-base-cased-distilled-squad |
| `summarization` | Summarization | sshleifer/distilbart-cnn-12-6 |
| `translation` | French to English | Helsinki-NLP/opus-mt-fr-en |
| `image` | Image classification | google/vit-base-patch16-224 |
| `speech` | Speech recognition, from a file or the microphone | openai/whisper-large-v3 |

## Notes

- The module sets `HF_HUB_OFFLINE=1` (unless it is already set), so models are read only from the
  local cache. Online, a model stored as `.bin` starts a background conversion to safetensors
  that can keep Python from exiting for minutes.
- Gradio is pinned to 4.44.1, the last version that runs on Python 3.9, and pydantic to 2.10.6,
  because Gradio 4.44 fails to start with pydantic 2.11 or later.
- The Gradio components that show scores (`gr.Label`) take a `{label: score}` dictionary, which is
  why most `run()` methods return one.
