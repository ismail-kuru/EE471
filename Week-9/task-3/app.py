"""Gradio demo of the ten Week 9 tasks, one tab each, built on the TransformerTasks module.

Usage: python app.py, then open http://127.0.0.1:7860
A model is loaded the first time its tab's Submit is pressed, so that first answer takes longer.
"""

import examples as ex
import gradio as gr
from transformer_tasks import TransformerTasks

tasks = TransformerTasks()


# Small adapters between the Gradio components and the module: they only convert formats.

def zero_shot(text, labels):
    return tasks.zero_shot.run(text, [label.strip() for label in labels.split(",") if label.strip()])


def generation(prompt, max_words, seed):
    options = tasks.generation.run(prompt, max_words=int(max_words), seed=int(seed))
    return "\n\n".join(f"Option {number} ({len(text.split())} words): {text}"
                       for number, text in enumerate(options, start=1))


def ner(text):
    entities = [{"entity": e["entity_group"], "start": e["start"], "end": e["end"]} for e in tasks.ner.run(text)]
    return {"text": text, "entities": entities}, tasks.ner.summary(text)


def qa(question, context):
    answer, score = tasks.qa.run(question, context)
    return answer, round(score, 4)


def summarization(text, max_length, min_length):
    return tasks.summarization.run(text, max_length=int(max_length), min_length=int(min_length))


def interface(function, inputs, outputs, examples):
    """One tab: inputs, outputs, Clear and Submit buttons and the Task 1 example. No Flag button."""
    return gr.Interface(function, inputs, outputs, examples=examples, allow_flagging="never")


def text_box(label, lines=3, value=None):
    return gr.Textbox(label=label, lines=lines, value=value)


interfaces = {
    "Sentiment analysis": interface(
        tasks.sentiment.run, text_box("Text", 2), gr.Label(label="Sentiment"),
        examples=ex.SENTIMENT),
    "Zero-shot classification": interface(
        zero_shot, [text_box("Text", 2), gr.Textbox(label="Labels, separated by commas")],
        gr.Label(label="Scores"),
        examples=[[ex.ZERO_SHOT, ", ".join(ex.ZERO_SHOT_LABELS)]]),
    "Text generation": interface(
        generation, [text_box("Start of a sentence", 2), gr.Slider(10, 60, value=35, step=1, label="Maximum words"),
                     gr.Number(value=42, label="Random seed")],
        text_box("Two alternative completions", 8),
        examples=[[ex.GENERATION, 35, 42]]),
    "Mask filling": interface(
        tasks.fill_mask.run, [text_box("Sentence with a gap: […], [MASK] or <mask>", 2),
                              gr.Slider(1, 10, value=5, step=1, label="Number of suggestions")],
        gr.Label(label="Completed sentences"),
        examples=[[ex.FILL_MASK, 5]]),
    "Named entity recognition": interface(
        ner, text_box("Text"), [gr.HighlightedText(label="Entities"), gr.JSON(label="Person, organization, location")],
        examples=[ex.NATE]),
    "Question answering": interface(
        qa, [gr.Textbox(label="Question"), text_box("Context")],
        [gr.Textbox(label="Answer"), gr.Number(label="Score")],
        examples=[[question, ex.NATE] for question in ex.QUESTIONS]),
    "Summarization": interface(
        summarization, [text_box("Text", 8), gr.Slider(20, 150, value=60, step=1, label="Maximum length (tokens)"),
                        gr.Slider(5, 60, value=20, step=1, label="Minimum length (tokens)")],
        text_box("Summary", 4),
        examples=[[ex.CRISIS_TEXT, 60, 20]]),
    "Translation (French to English)": interface(
        tasks.translation.run, text_box("French"), text_box("English"),
        examples=[ex.TRANSLATION]),
    "Image classification": interface(
        tasks.image.run, [gr.Image(type="filepath", label="Image"),
                          gr.Slider(1, 10, value=5, step=1, label="Number of classes")],
        gr.Label(label="ImageNet classes"),
        examples=[[ex.IMAGE, 5]]),
    "Speech recognition": interface(
        tasks.speech.run, gr.Audio(type="filepath", sources=["upload", "microphone"], label="Audio"),
        text_box("Transcription"),
        examples=[ex.AUDIO]),
}

demo = gr.TabbedInterface(list(interfaces.values()), list(interfaces), title="Week 9: Transformers pipelines")

if __name__ == "__main__":
    demo.launch()
