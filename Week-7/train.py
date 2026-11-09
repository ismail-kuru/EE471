"""Train a classifier and save its weights and results.

Example:
    python train.py --dataset fashion --lr 0.001 --batch-size 64 --epochs 5 -o runs/fashion-baseline
"""

import argparse
import json
import sys
import time
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader

from model.models import DATASETS

DATA_DIR = Path(__file__).resolve().parent / "data"


def parse_args():
    parser = argparse.ArgumentParser(description="Train a classifier.")
    parser.add_argument("--dataset", required=True, choices=DATASETS)
    parser.add_argument("--lr", type=float, default=1e-3, help="learning rate")
    parser.add_argument("--momentum", type=float, default=0.0, help="SGD momentum")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--shuffle", action="store_true", help="mix the training images every epoch")
    parser.add_argument("--seed", type=int, default=0, help="makes a run repeatable")
    parser.add_argument("-o", "--output", required=True, type=Path, help="folder for the results")
    return parser.parse_args()


def get_device():
    """Use the GPU if there is one (MPS on Apple Silicon), otherwise the CPU."""
    return torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"


def load_data(settings, batch_size, shuffle=False):
    """Download the dataset if needed and return its training and test batches."""
    train_data = settings["loader"](root=DATA_DIR, train=True, download=True, transform=settings["transform"])
    test_data = settings["loader"](root=DATA_DIR, train=False, download=True, transform=settings["transform"])
    return DataLoader(train_data, batch_size=batch_size, shuffle=shuffle), DataLoader(test_data, batch_size=batch_size)


def train_one_epoch(model, loader, loss_fn, optimizer, device):
    """Show the model every training image once, updating its weights after each batch."""
    model.train()
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        loss = loss_fn(model(images), labels)  # How wrong is the model on this batch?
        loss.backward()                        # Which way should each weight change?
        optimizer.step()                       # Change the weights a little.
        optimizer.zero_grad()                  # Clear the gradients for the next batch.


def evaluate(model, loader, loss_fn, device, classes):
    """Return the loss and accuracy on data the model did not train on."""
    model.eval()
    total_loss = correct = 0
    class_correct = [0] * len(classes)
    class_total = [0] * len(classes)
    with torch.no_grad():  # Testing changes no weights, so gradients are not needed.
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            total_loss += loss_fn(outputs, labels).item() * len(labels)
            hits = outputs.argmax(1) == labels
            correct += hits.sum().item()
            for label, hit in zip(labels.tolist(), hits.tolist()):
                class_total[label] += 1
                class_correct[label] += hit
    count = len(loader.dataset)
    return {
        "loss": total_loss / count,
        "accuracy": correct / count,
        "per_class_accuracy": {
            name: class_correct[i] / class_total[i] for i, name in enumerate(classes)
        },
    }


def main():
    args = parse_args()
    weights_file = args.output / "model.pth"
    if weights_file.exists():
        sys.exit(f"{weights_file} already exists. Choose another folder with -o.")
    args.output.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(args.seed)
    settings = DATASETS[args.dataset]
    device = get_device()
    print(f"Dataset: {args.dataset}, device: {device}")

    train_loader, test_loader = load_data(settings, args.batch_size, args.shuffle)
    model = settings["model"]().to(device)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=args.momentum)

    history = []
    started = time.time()
    for epoch in range(1, args.epochs + 1):
        train_one_epoch(model, train_loader, loss_fn, optimizer, device)
        result = evaluate(model, test_loader, loss_fn, device, settings["classes"])
        history.append({"epoch": epoch, "loss": result["loss"], "accuracy": result["accuracy"]})
        print(f"Epoch {epoch}/{args.epochs}: accuracy {result['accuracy']:.1%}, loss {result['loss']:.4f}")
    seconds = time.time() - started

    torch.save(model.state_dict(), weights_file)
    metrics = {
        "dataset": args.dataset,
        "classes": settings["classes"],
        "hyperparameters": {
            "lr": args.lr, "momentum": args.momentum, "batch_size": args.batch_size, "epochs": args.epochs,
            "shuffle": args.shuffle, "seed": args.seed,
        },
        "accuracy": result["accuracy"],
        "loss": result["loss"],
        "per_class_accuracy": result["per_class_accuracy"],
        "history": history,
        "training_seconds": round(seconds, 1),
        "device": device,
    }
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"Saved {weights_file}. Test accuracy: {result['accuracy']:.1%} in {seconds:.0f} seconds.")


if __name__ == "__main__":
    main()
