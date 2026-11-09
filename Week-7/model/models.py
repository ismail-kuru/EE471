"""The neural networks and the settings of each dataset."""

import torch
from torch import nn
from torchvision import datasets
from torchvision.transforms import v2


class NeuralNetwork(nn.Module):
    """The fully connected network from the PyTorch Quickstart tutorial."""

    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28 * 28, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 10),
        )

    def forward(self, x):
        x = self.flatten(x)
        return self.linear_relu_stack(x)


# Everything that differs between datasets lives here, so train.py works for all of them.
DATASETS = {
    "fashion": {
        "loader": datasets.FashionMNIST,
        "model": NeuralNetwork,
        # Turns a picture into a tensor with values from 0 to 1.
        "transform": v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)]),
        # What the model was trained on: small gray pictures with a dark background.
        "image_mode": "L",
        "image_size": 28,
        "dark_background": True,
        "classes": [
            "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
            "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot",
        ],
    },
}
