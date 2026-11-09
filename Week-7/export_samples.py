"""Save test images, which the models never trained on, to try on the website.

Usage: python export_samples.py fashion
"""

import sys
from pathlib import Path

from model.models import DATASETS
from train import DATA_DIR

SAMPLES_PER_CLASS = 2

name = sys.argv[1] if len(sys.argv) == 2 else sys.exit("Usage: python export_samples.py <dataset>")
settings = DATASETS[name]
test_data = settings["loader"](root=DATA_DIR, train=False, download=True)

output = Path(__file__).resolve().parent / "samples" / name
output.mkdir(parents=True, exist_ok=True)

saved = [0] * len(settings["classes"])
for picture, label in test_data:
    if saved[label] < SAMPLES_PER_CLASS:
        saved[label] += 1
        class_name = settings["classes"][label].replace("/", "-").replace(" ", "-").lower()
        picture.save(output / f"{class_name}-{saved[label]}.png")
print(f"Saved {sum(saved)} images to {output}")
