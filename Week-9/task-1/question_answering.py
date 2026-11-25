"""Task 1.6: check the person, organization and city found by NER by asking questions about the sentence."""

from common import show, title
from named_entity_recognition import SENTENCE, extract
from transformers import pipeline

QUESTIONS = {
    "person": "What is my name?",
    "organization": "Where do I work?",
    "city": "In which city do I live?",
}

_, found = extract()
question_answerer = pipeline("question-answering")  # default: distilbert-base-cased-distilled-squad

title("Question answering, validating the NER results")
show("Context", SENTENCE)
for key, question in QUESTIONS.items():
    answer = question_answerer(question=question, context=SENTENCE)
    match = "match" if answer["answer"].strip(" .,") == found[key] else "DIFFERENT"
    print()
    show("Question", question)
    show("QA", f"{answer['answer']} ({answer['score']:.4f})")
    show("NER", f"{found[key]}  ->  {match}")
