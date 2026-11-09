"""Serve one trained classifier with Cog. MODEL_NAME chooses which weights to load."""

import json
import logging
import os
from pathlib import Path as FilePath

import torch
from cog import BaseRunner, Input, Path
from PIL import Image, ImageOps, ImageStat

from models import DATASETS

WEIGHTS_DIR = FilePath(__file__).resolve().parent / "weights"
TOP_CLASSES = 3

# Every prediction is written here, so it can be followed from inside the container.
LOG_FILE = "/tmp/predictions.log"


def prepare_image(picture, settings):
    """Make an uploaded picture look like the pictures the model was trained on."""
    size = settings["image_size"]
    picture = ImageOps.exif_transpose(picture).convert(settings["image_mode"])
    # Fit the picture in a square, filling the empty sides with its corner color.
    picture = ImageOps.pad(picture, (size, size), color=picture.getpixel((0, 0)))
    if settings["dark_background"]:
        # A normal photo has a light background, so swap light and dark to match the training data.
        border = picture.crop((0, 0, size, 1))
        if ImageStat.Stat(border).mean[0] > 127:
            picture = ImageOps.invert(picture)
    return picture


class Runner(BaseRunner):
    def setup(self):
        """Load the model once, so every prediction after this is fast."""
        logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s %(message)s")
        self.log = logging.getLogger("predictions")

        self.name = os.environ["MODEL_NAME"]
        self.metrics = json.loads((WEIGHTS_DIR / f"{self.name}.json").read_text())
        self.settings = DATASETS[self.metrics["dataset"]]

        self.model = self.settings["model"]()
        weights = torch.load(WEIGHTS_DIR / f"{self.name}.pth", map_location="cpu", weights_only=True)
        self.model.load_state_dict(weights)
        self.model.eval()
        self.log.info("Model %s loaded (test accuracy %.1f%%)", self.name, self.metrics["accuracy"] * 100)

    def run(self, image: Path = Input(description="Image to classify")) -> dict:
        """Return the predicted class, its probability and the most likely classes."""
        picture = Image.open(image)
        self.log.info("Received image: %dx%d pixels", *picture.size)

        batch = self.settings["transform"](prepare_image(picture, self.settings)).unsqueeze(0)
        with torch.no_grad():
            probabilities = self.model(batch)[0].softmax(0)

        classes = self.settings["classes"]
        best = probabilities.topk(TOP_CLASSES)
        top_classes = [
            {"class": classes[i], "probability": p}
            for p, i in zip(best.values.tolist(), best.indices.tolist())
        ]
        predicted = top_classes[0]
        self.log.info(
            "Model %s predicted %s (%.1f%%)",
            self.name, predicted["class"], predicted["probability"] * 100,
        )
        return {
            "model": self.name,
            "test_accuracy": self.metrics["accuracy"],
            "hyperparameters": self.metrics["hyperparameters"],
            "predicted_class": predicted["class"],
            "confidence": predicted["probability"],
            "top_classes": top_classes,
        }
