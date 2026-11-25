"""Task 1.7: summarize a paragraph about the 2008 financial crisis."""

import textwrap

from common import show, title
from transformers import pipeline

TEXT = (
    "The 2008 Global Financial Crisis stands as the most severe economic collapse of the 21st century, "
    "often compared to the Great Depression of the 1930s. Triggered by the bursting of the United States "
    "housing bubble, its effects rippled across the globe, leading to the collapse of major financial "
    "institutions and a deep international recession. The crisis began with the subprime mortgage market. "
    "In the early 2000s, low interest rates and a push for homeownership led banks to issue high-risk loans "
    "to borrowers with poor credit."
)

summarizer = pipeline("summarization")  # default: sshleifer/distilbart-cnn-12-6
summary = summarizer(TEXT, max_length=60, min_length=41)[0]["summary_text"]
summary = summary.replace(" .", ".").strip()  # distilbart-cnn puts a space before each full stop

title("Summarization")
print(textwrap.fill(f"Text ({len(TEXT.split())} words): {TEXT}", 100))
print()
print(textwrap.fill(f"Summary ({len(summary.split())} words): {summary}", 100))
