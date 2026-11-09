"""The neural networks and the settings of each dataset."""

import torch
import torch.nn.functional as F
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


class Net(nn.Module):
    """The small convolutional network from the PyTorch CIFAR10 tutorial."""

    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = torch.flatten(x, 1)  # Flatten all dimensions except the batch.
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


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
        # The values tune.py tries. Around and above the tutorial's lr 0.001 and batch size 64.
        "search": {"learning_rates": [0.001, 0.01, 0.1], "batch_sizes": [32, 64, 128], "momentum": 0.0, "max_epochs": 15},
    },
    "cifar10": {
        "loader": datasets.CIFAR10,
        "model": Net,
        # Turns a picture into a tensor with values from -1 to 1.
        "transform": v2.Compose([
            v2.ToImage(),
            v2.ToDtype(torch.float32, scale=True),
            v2.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ]),
        # What the model was trained on: small color photos with any background.
        "image_mode": "RGB",
        "image_size": 32,
        "dark_background": False,
        "classes": ["plane", "car", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"],
        # The tutorial's momentum stays. Higher learning rates are unstable with it, so the values stay small.
        "search": {"learning_rates": [0.001, 0.003, 0.01], "batch_sizes": [32, 64], "momentum": 0.9, "max_epochs": 12},
    },
}
