"""Text Summarizer: shortens a long text into a one or two sentence summary, or into key points.

Usage: python text_summarizer.py [file.txt]   (default: the text below)
Model: a 200M-parameter Gemma-based model with two modes: TLDR (1-2 sentences) and KEYPOINTS
(3-5 bullet points). It runs on the computer, without an internet service.
"""

import sys
from pathlib import Path

from mediapipe.tasks.python import BaseOptions, text

from common import model

ARTICLE = (
    "This week in EE 471 we worked with MediaPipe, Google's library for on-device machine learning. "
    "First, we tried its ready-made solutions in Python: detecting faces, hands and body poses, "
    "classifying images and sounds, segmenting objects, and newer language tasks such as transcribing "
    "speech, generating speech, proofreading and summarizing text. Then we used the pose landmarker to "
    "decide which arm a person raises, comparing the wrist with the shoulder. We also used the face "
    "landmarker to decide whether a face looks left, right or straight, from the head's rotation angle. "
    "Both scripts were packaged with Cog into Docker images, so they run the same way on any computer "
    "and can be called from the command line or over HTTP."
)
article = Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else ARTICLE
print(f"Original: {len(article.split())} words\n")

for mode in (text.TextSummarizerMode.TLDR, text.TextSummarizerMode.KEYPOINTS):
    options = text.TextSummarizerOptions(
        base_options=BaseOptions(model_asset_path=model("summarization_quant_200m_2modes.litertlm")),
        mode=mode,
    )
    with text.TextSummarizer.create_from_options(options) as summarizer:
        summary = summarizer.summarize(article).summary
    print(f"{mode.name}:\n{summary}\n")
