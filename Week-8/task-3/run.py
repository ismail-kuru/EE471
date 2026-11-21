"""Cog entry point: takes an image and returns which way the face is looking."""

from cog import BaseRunner, Input, Path

from face_direction import classify, create_landmarker

# cog.yaml downloads the model here while the image is built.
MODEL_PATH = "/opt/models/face_landmarker.task"


class Runner(BaseRunner):
    def setup(self):
        """Load the face model once, when the container starts."""
        self.landmarker = create_landmarker(MODEL_PATH)

    def run(self, image: Path = Input(description="Photo of a face")) -> str:
        """Return "left", "right" or "straight"."""
        return classify(image, self.landmarker)
