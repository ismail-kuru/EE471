"""Small helpers shared by the Task 4 scripts: the model they use and readable printing."""

import os
import warnings
from pathlib import Path

# Every model is already in the cache (download_models.py), so never go online, and keep the
# terminal clean for the screen recordings. Both must be set before transformers is imported.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
warnings.filterwarnings("ignore")

from transformers.utils import logging  # noqa: E402

logging.set_verbosity_error()
logging.disable_progress_bar()

# The model of the course's chapter 2 ("Behind the pipeline"): the sentiment-analysis default.
# download_models.py fetched it at this revision, so it is loaded at the same one.
CHECKPOINT = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
REVISION = "714eb0f"
HERE = Path(__file__).resolve().parent


def title(text):
    print(f"\n=== {text}\n")


def show(label, value):
    print(f"{label:>16}: {value}")
