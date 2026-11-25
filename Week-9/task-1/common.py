"""Small helpers shared by the Task 1 scripts: sample paths and readable printing."""

import os
import sys
import warnings
from pathlib import Path

# Every model is already in the cache (download_models.py), so never go online. Without this,
# loading a model stored as .bin starts a background check for a safetensors copy on the Hub; on a
# slow connection that thread keeps Python from exiting after the script has finished.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

# Keep the terminal clean for the screen recordings: hide library warnings and progress bars.
# The filter must be set before transformers is imported, which is why this file is imported first.
warnings.filterwarnings("ignore")

from transformers.utils import logging  # noqa: E402

SAMPLES = Path(__file__).resolve().parent.parent / "samples"

logging.set_verbosity_error()
logging.disable_progress_bar()


def input_path(default):
    """The file given on the command line, or the default sample."""
    return Path(sys.argv[1]) if len(sys.argv) > 1 else SAMPLES / default


def title(text):
    print(f"\n=== {text}\n")


def show(label, value):
    print(f"{label:>12}: {value}")
