"""Task 1.8: translate a French sentence into English."""

from common import show, title
from transformers import pipeline

SENTENCE = "Ce cours est produit par Hugging Face."

translator = pipeline("translation", model="Helsinki-NLP/opus-mt-fr-en")

title("Translation, French to English")
show("French", SENTENCE)
show("English", translator(SENTENCE)[0]["translation_text"])
