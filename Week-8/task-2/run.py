"""Cog entry point: takes an image and returns which arm is raised."""

from cog import BaseRunner, Input, Path

from arm_up import classify, create_landmarker

# cog.yaml downloads the model here while the image is built.
MODEL_PATH = "/opt/models/pose_landmarker_full.task"


class Runner(BaseRunner):
    def setup(self):
        """Load the pose model once, when the container starts."""
        self.landmarker = create_landmarker(MODEL_PATH)

    def run(self, image: Path = Input(description="Photo of a person")) -> str:
        """Return "left", "right", "both" or "None"."""
        return classify(image, self.landmarker)
