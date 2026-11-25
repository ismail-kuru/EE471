# Week 9, Task 1: Transformers pipelines

The ten tasks of the in-class exercise, one short script each, built on `pipeline()` from the
[Hugging Face LLM course, chapter 1.3](https://huggingface.co/learn/llm-course/chapter1/3).

## Run

From the `Week-9` folder, after `download_models.py` (see `../README.md`):

```bash
cd task-1
../.venv/bin/python sentiment_analysis.py
HF_HUB_OFFLINE=1 ../.venv/bin/python translation.py      # every script also works offline
../.venv/bin/python image_classification.py my_photo.jpg  # the image and audio scripts take a file
```

## The tasks

| Script | Task | Model | Result |
|---|---|---|---|
| `sentiment_analysis.py` | Sentiment of two sentences | distilbert-base-uncased-finetuned-sst-2-english | both NEGATIVE (0.99, 0.89) |
| `zero_shot_classification.py` | "Berkshire keeps their cash reserves…" against 5 labels | facebook/bart-large-mnli | finance 0.91 |
| `text_generation.py` | Two completions of "If I continue to complete all in-class exercises…", at most 35 words | HuggingFaceTB/SmolLM2-360M | `max_length=35`: 30 and 27 words, cut mid-sentence; fixed: 34 and 24 words, complete |
| `fill_mask.py` | "To understand generative AI, one must study `<mask>` well." | distilroberta-base | AI, it, them, algorithms, very |
| `named_entity_recognition.py` | Person, organization and city in the sentence about Nate | bert-large-cased-finetuned-conll03-english | Nate, Izmir Institute of Technology, İzmir |
| `question_answering.py` | Checks the three NER results with three questions | distilbert-base-cased-distilled-squad | all three match |
| `summarization.py` | Summary of the 2008 financial crisis paragraph | sshleifer/distilbart-cnn-12-6 | 85 words to 40 |
| `translation.py` | "Ce cours est produit par Hugging Face.", French to English | Helsinki-NLP/opus-mt-fr-en | "This course is produced by Hugging Face." |
| `image_classification.py` | Top 5 ImageNet classes of an image | google/vit-base-patch16-224 | lynx 0.43 (a big fluffy cat) |
| `speech_recognition.py` | Transcription of an audio clip | openai/whisper-large-v3 | "I have a dream that one day this nation will rise up…" |

## Notes

- **Sentiment:** the model calls the first sentence negative, although it is meant positively. The
  course's own sentence ("…waiting for a HuggingFace course my whole life.") comes out positive,
  so the words "modern software practices course" are what change the result.
- **Text generation:** the script runs the model twice to show why the plain way does not work.
  1. `max_length=35` counts **tokens, not words**, and it **includes the prompt**. The prompt is
     14 words but 17 tokens ("in-class" alone is 3: `in`, `-`, `class`), so only 18 new tokens are
     left and both sentences stop in the middle ("…types of errors in my", "…The TOEFL exam").
     The pipeline also sets `max_new_tokens=256` by default, which wins over `max_length`, so
     `max_length=35` on its own is silently ignored (194 words came out). The script passes
     `max_new_tokens=None` to turn that default off.
  2. The fixed way: `max_new_tokens=50` counts only new tokens, so the model has room to finish
     its sentence, then `shorten()` counts real words, keeps at most 35 and goes back to the last
     full sentence. Result: 34 and 24 words, both complete.

  Sampling (`do_sample=True`) is what makes the two options different; it is random, so
  `set_seed(42)` keeps them the same on every run.
- **Question answering:** the script runs the NER script first and prints `match` when the answer
  is the same entity.
- **Whisper:** the downloaded weights are float16, which gives garbage ("!") on the Mac GPU (MPS).
  Loading the model as float32 fixes it.
- `common.py` hides library warnings and progress bars so the output is easy to read in the videos.
