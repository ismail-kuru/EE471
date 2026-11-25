"""The 11 pipeline() examples from the Hugging Face LLM course, chapter 1.3 ("Transformers, what can they do?").

Usage: python pipelines_demo.py            run every example
       python pipelines_demo.py ner        run one (sentiment, zero-shot, generation, smollm, fill-mask,
                                           ner, qa, summarization, translation, image, speech)
Run download_models.py first. The models are then read from the local cache, so this also works
without internet: HF_HUB_OFFLINE=1 python pipelines_demo.py
"""

import sys
from pathlib import Path

import torch
from transformers import pipeline

SAMPLES = Path(__file__).resolve().parent / "samples"


def sentiment():
    classifier = pipeline("sentiment-analysis")
    return classifier(["I've been waiting for a HuggingFace course my whole life.", "I hate this so much!"])


def zero_shot():
    classifier = pipeline("zero-shot-classification")
    return classifier("This is a course about the Transformers library",
                      candidate_labels=["education", "politics", "business"])


def generation():
    generator = pipeline("text-generation")
    return generator("In this course, we will teach you how to")


def smollm():
    generator = pipeline("text-generation", model="HuggingFaceTB/SmolLM2-360M")
    return generator("In this course, we will teach you how to", max_length=30, num_return_sequences=2)


def fill_mask():
    unmasker = pipeline("fill-mask")
    return unmasker("This course will teach you all about <mask> models.", top_k=2)


def ner():
    recognizer = pipeline("ner", grouped_entities=True)
    return recognizer("My name is Sylvain and I work at Hugging Face in Brooklyn.")


def qa():
    question_answerer = pipeline("question-answering")
    return question_answerer(question="Where do I work?",
                             context="My name is Sylvain and I work at Hugging Face in Brooklyn")


def summarization():
    summarizer = pipeline("summarization")
    # A short text of our own; the course page uses a longer one about engineering education.
    return summarizer(
        "The Transformers library gives access to thousands of pretrained models for text, images and "
        "audio. Its pipeline function connects a model with the steps it needs before and after: it "
        "turns raw text into numbers the model understands, runs the model, and turns the output back "
        "into readable results. With a single line of code, a pipeline can classify sentiment, answer "
        "questions, translate between languages, summarize long documents, describe images or transcribe "
        "speech. Models are downloaded from the Hugging Face Hub the first time they are used and stored "
        "in a local cache, so later runs are fast and can even work offline."
    )


def translation():
    translator = pipeline("translation", model="Helsinki-NLP/opus-mt-fr-en")
    return translator("Ce cours est produit par Hugging Face.")


def image():
    image_classifier = pipeline(task="image-classification", model="google/vit-base-patch16-224")
    return image_classifier(str(SAMPLES / "pipeline-cat-chonk.jpeg"))


def speech():
    # The weights are float16, which gives garbage on the Mac GPU (MPS); float32 works.
    transcriber = pipeline(task="automatic-speech-recognition", model="openai/whisper-large-v3",
                           dtype=torch.float32)
    return transcriber(str(SAMPLES / "mlk.flac"))


EXAMPLES = {
    "sentiment": sentiment, "zero-shot": zero_shot, "generation": generation, "smollm": smollm,
    "fill-mask": fill_mask, "ner": ner, "qa": qa, "summarization": summarization,
    "translation": translation, "image": image, "speech": speech,
}

if __name__ == "__main__":
    chosen = sys.argv[1:] or list(EXAMPLES)
    for name in chosen:
        print(f"\n=== {name}")
        print(EXAMPLES[name]())
