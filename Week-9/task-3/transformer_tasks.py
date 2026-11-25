"""An object-oriented wrapper around Hugging Face pipelines for the ten tasks of Week 9.

Every task is a class with a run() method. The model behind it is loaded the first time run() is
called and then kept, so a task that is never used never loads its model, and a task used many
times loads it only once.

    from transformer_tasks import TransformerTasks
    tasks = TransformerTasks()
    tasks.sentiment.run("I hate software courses")   # {'NEGATIVE': 0.89, 'POSITIVE': 0.11}

Run this file to send the Task 1 inputs through every task: python transformer_tasks.py
"""

import os
import re
import warnings

# Both settings must be made before transformers is imported.
# Use only the downloaded models. Online, loading a model stored as .bin starts a background
# conversion to safetensors that keeps Python from exiting until it ends, which can take minutes.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
# Hide library warnings and progress bars.
warnings.filterwarnings("ignore")

import torch  # noqa: E402
from transformers import pipeline, set_seed  # noqa: E402
from transformers.utils import logging  # noqa: E402

logging.set_verbosity_error()
logging.disable_progress_bar()


class Task:
    """One pipeline task. Subclasses set the class attributes and write run()."""

    task = ""       # the pipeline() task name, e.g. "sentiment-analysis"
    model = None    # a model name on the Hugging Face Hub, or None for the pipeline's default
    options = {}    # extra arguments for pipeline(), e.g. the data type

    def __init__(self):
        self._pipeline = None

    @property
    def pipeline(self):
        """The Hugging Face pipeline, created on first use and reused after that."""
        if self._pipeline is None:
            self._pipeline = pipeline(self.task, model=self.model, **self.options)
        return self._pipeline

    @property
    def model_name(self):
        """The name of the model actually used, also when the pipeline picked its default."""
        return self.pipeline.model.name_or_path

    def run(self, *inputs):
        raise NotImplementedError


class SentimentAnalysis(Task):
    task = "sentiment-analysis"  # default: distilbert-base-uncased-finetuned-sst-2-english

    def run(self, text):
        """Return the score of every label, e.g. {'POSITIVE': 0.96, 'NEGATIVE': 0.04}."""
        results = self.pipeline(text, top_k=None)  # top_k=None: all labels, not only the best one
        return {result["label"]: result["score"] for result in results}


class ZeroShotClassification(Task):
    task = "zero-shot-classification"  # default: facebook/bart-large-mnli

    def run(self, text, labels):
        """Score the text against labels the model was never trained on."""
        result = self.pipeline(text, candidate_labels=labels)
        return dict(zip(result["labels"], result["scores"]))


class TextGeneration(Task):
    task = "text-generation"
    model = "HuggingFaceTB/SmolLM2-360M"

    def run(self, prompt, max_words=35, count=2, seed=42):
        """Return `count` different continuations of the prompt, each at most max_words words."""
        set_seed(seed)  # sampling is random; the same seed gives the same texts
        results = self.pipeline(prompt, max_new_tokens=2 * max_words, num_return_sequences=count,
                                do_sample=True)
        return [self.shorten(result["generated_text"], max_words, len(prompt)) for result in results]

    @staticmethod
    def shorten(text, max_words, prompt_length):
        """Cut the text to max_words words, then back to the last full sentence after the prompt."""
        words = " ".join(text.split()[:max_words])
        end = max(words.rfind("."), words.rfind("!"), words.rfind("?"))
        return words[: end + 1] if end > prompt_length else words


class FillMask(Task):
    task = "fill-mask"  # default: distilroberta-base

    # Ways people write the gap; all of them become the model's own mask token.
    GAPS = re.compile(r"\[\s*(…|\.\.\.)\s*\]|\[MASK\]|<mask>|___+")

    def run(self, text, top_k=5):
        """Return the top_k completed sentences with their scores."""
        text = self.GAPS.sub(self.pipeline.tokenizer.mask_token, text)
        return {result["sequence"]: result["score"] for result in self.pipeline(text, top_k=top_k)}


class NamedEntityRecognition(Task):
    task = "ner"  # default: dbmdz/bert-large-cased-finetuned-conll03-english
    options = {"aggregation_strategy": "simple"}  # join word pieces into whole names

    def run(self, text):
        """Return the entities, each with its type (PER, ORG, LOC, MISC), word, score and position."""
        return self.pipeline(text)

    def summary(self, text):
        """The first person, organization and location in the text."""
        first = {}
        for entity in self.run(text):
            first.setdefault(entity["entity_group"], entity["word"])
        return {"person": first.get("PER"), "organization": first.get("ORG"), "location": first.get("LOC")}


class QuestionAnswering(Task):
    task = "question-answering"  # default: distilbert-base-cased-distilled-squad

    def run(self, question, context):
        """Return the answer, copied out of the context, and the model's confidence."""
        result = self.pipeline(question=question, context=context)
        return result["answer"], result["score"]


class Summarization(Task):
    task = "summarization"  # default: sshleifer/distilbart-cnn-12-6

    def run(self, text, max_length=60, min_length=20):
        """Return a summary between min_length and max_length tokens long."""
        summary = self.pipeline(text, max_length=max_length, min_length=min_length)[0]["summary_text"]
        return summary.replace(" .", ".").strip()  # this model puts a space before each full stop


class Translation(Task):
    task = "translation"
    model = "Helsinki-NLP/opus-mt-fr-en"  # French to English

    def run(self, text):
        return self.pipeline(text)[0]["translation_text"]


class ImageClassification(Task):
    task = "image-classification"
    model = "google/vit-base-patch16-224"

    def run(self, image, top_k=5):
        """Return the top_k of the 1000 ImageNet classes. `image` is a file path or a PIL image."""
        return {result["label"]: result["score"] for result in self.pipeline(image, top_k=top_k)}


class SpeechRecognition(Task):
    task = "automatic-speech-recognition"
    model = "openai/whisper-large-v3"
    # The downloaded weights are float16, which gives garbage ("!") on the Mac GPU (MPS); float32 works.
    options = {"dtype": torch.float32}

    def run(self, audio):
        """Return the text spoken in an audio file."""
        return self.pipeline(audio)["text"].strip()


class TransformerTasks:
    """All ten tasks in one object. Nothing is loaded until a task is first used."""

    def __init__(self):
        self.sentiment = SentimentAnalysis()
        self.zero_shot = ZeroShotClassification()
        self.generation = TextGeneration()
        self.fill_mask = FillMask()
        self.ner = NamedEntityRecognition()
        self.qa = QuestionAnswering()
        self.summarization = Summarization()
        self.translation = Translation()
        self.image = ImageClassification()
        self.speech = SpeechRecognition()


if __name__ == "__main__":
    import examples as ex

    tasks = TransformerTasks()
    print("sentiment     ", [tasks.sentiment.run(text) for text in ex.SENTIMENT])
    print("zero-shot     ", tasks.zero_shot.run(ex.ZERO_SHOT, ex.ZERO_SHOT_LABELS))
    print("generation    ", tasks.generation.run(ex.GENERATION))
    print("fill-mask     ", tasks.fill_mask.run(ex.FILL_MASK, top_k=3))
    print("ner           ", tasks.ner.summary(ex.NATE))
    print("qa            ", [tasks.qa.run(question, ex.NATE) for question in ex.QUESTIONS])
    print("summarization ", tasks.summarization.run(ex.CRISIS_TEXT))
    print("translation   ", tasks.translation.run(ex.TRANSLATION))
    print("image         ", tasks.image.run(ex.IMAGE, top_k=3))
    print("speech        ", tasks.speech.run(ex.AUDIO))
