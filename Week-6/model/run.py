"""Cat-kind classifier: Cog's pre-trained ResNet-50, reduced to the cat classes it knows."""

import logging
import os

# The weights were stored here when the image was built (see cog.yaml).
os.environ["TORCH_HOME"] = "/opt/torch"

import torch
from cog import BaseRunner, Input, Path
from PIL import Image
from torchvision import models

WEIGHTS = models.ResNet50_Weights.IMAGENET1K_V1

# The ImageNet classes that are kinds of cat.
CAT_KINDS = {
    "tabby", "tiger cat", "Persian cat", "Siamese cat", "Egyptian cat",
    "cougar", "lynx", "leopard", "snow leopard", "jaguar", "lion", "tiger", "cheetah",
}
# The image counts as a cat if the cat classes together get at least this probability.
CAT_THRESHOLD = 0.5
TOP_KINDS = 3

# Every prediction is written here, so it can be followed from inside the container.
LOG_FILE = "/tmp/predictions.log"


class Runner(BaseRunner):
    def setup(self):
        """Load the model once, so every prediction after this is fast."""
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format="%(asctime)s %(message)s",
        )
        self.log = logging.getLogger("predictions")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet50(weights=WEIGHTS).to(self.device)
        self.model.eval()
        self.categories = WEIGHTS.meta["categories"]
        self.log.info("Model loaded on %s", self.device)

    def run(self, image: Path = Input(description="Image of a cat to classify")) -> dict:
        """Return the predicted class, its probability and the most likely cat kinds."""
        picture = Image.open(image).convert("RGB")
        self.log.info("Received image: %dx%d pixels", *picture.size)

        batch = WEIGHTS.transforms()(picture).unsqueeze(0).to(self.device)
        with torch.no_grad():
            probabilities = self.model(batch)[0].softmax(0)

        scores = {name: probabilities[i].item() for i, name in enumerate(self.categories)}
        kinds = sorted(CAT_KINDS, key=scores.get, reverse=True)
        is_cat = sum(scores[kind] for kind in CAT_KINDS) >= CAT_THRESHOLD
        predicted_class = kinds[0] if is_cat else max(scores, key=scores.get)

        self.log.info(
            "Prediction: %s (%.1f%%), is_cat=%s",
            predicted_class, scores[predicted_class] * 100, is_cat,
        )
        return {
            "predicted_class": predicted_class,
            "confidence": scores[predicted_class],
            "is_cat": is_cat,
            # A list, because the order would be lost in a JSON object.
            "top_kinds": [{"kind": kind, "probability": scores[kind]} for kind in kinds[:TOP_KINDS]],
        }
