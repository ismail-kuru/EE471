"""Find good hyperparameters with a grid search: try every combination and compare them.

The test images are never used here. Each combination trains on part of the training images and
is scored on the rest (the validation images), so the final test score stays a fair measure.

Usage: python tune.py --dataset fashion -o tuning/fashion.json
"""

import argparse
import itertools
import json
import time
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, random_split

from model.models import DATASETS
from train import DATA_DIR, evaluate, get_device, train_one_epoch

# The values to try. Each is around or above the tutorial's values (lr 0.001, batch size 64).
LEARNING_RATES = [0.001, 0.01, 0.1]
BATCH_SIZES = [32, 64, 128]
# Every combination trains this long; the best epoch of each one is used as its epoch count.
MAX_EPOCHS = 15
VALIDATION_IMAGES = 10000
SEED = 0


def try_combination(settings, train_part, validation_loader, lr, batch_size, device):
    """Train with these values and return the validation accuracy after every epoch."""
    torch.manual_seed(SEED)  # Every combination starts from the same random weights.
    model = settings["model"]().to(device)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    train_loader = DataLoader(train_part, batch_size=batch_size, shuffle=True)

    accuracies = []
    for _ in range(MAX_EPOCHS):
        train_one_epoch(model, train_loader, loss_fn, optimizer, device)
        accuracies.append(evaluate(model, validation_loader, loss_fn, device, settings["classes"])["accuracy"])
    return accuracies


def main():
    parser = argparse.ArgumentParser(description="Search for good hyperparameters.")
    parser.add_argument("--dataset", required=True, choices=DATASETS)
    parser.add_argument("-o", "--output", required=True, type=Path, help="JSON file for the results")
    args = parser.parse_args()

    settings = DATASETS[args.dataset]
    device = get_device()
    all_training = settings["loader"](root=DATA_DIR, train=True, download=True, transform=settings["transform"])
    # The same images go to validation for every combination, so their scores can be compared.
    train_part, validation_part = random_split(
        all_training,
        [len(all_training) - VALIDATION_IMAGES, VALIDATION_IMAGES],
        generator=torch.Generator().manual_seed(SEED),
    )
    validation_loader = DataLoader(validation_part, batch_size=256)

    results = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for lr, batch_size in itertools.product(LEARNING_RATES, BATCH_SIZES):
        started = time.time()
        accuracies = try_combination(settings, train_part, validation_loader, lr, batch_size, device)
        best_accuracy = max(accuracies)
        results.append({
            "lr": lr,
            "batch_size": batch_size,
            "best_epoch": accuracies.index(best_accuracy) + 1,
            "validation_accuracy": best_accuracy,
            "accuracy_per_epoch": accuracies,
            "seconds": round(time.time() - started, 1),
        })
        print(
            f"lr={lr:<6} batch={batch_size:<4} best validation accuracy {best_accuracy:.1%} "
            f"at epoch {results[-1]['best_epoch']} ({results[-1]['seconds']:.0f}s)",
            flush=True,
        )
        # Saved after every combination, so an interrupted search keeps its results.
        args.output.write_text(json.dumps({"dataset": args.dataset, "max_epochs": MAX_EPOCHS, "results": results}, indent=2))

    best = max(results, key=lambda result: result["validation_accuracy"])
    print(
        f"\nBest: lr={best['lr']}, batch size={best['batch_size']}, epochs={best['best_epoch']} "
        f"({best['validation_accuracy']:.1%} validation accuracy)"
    )
    print(
        f"Train the final model with:\npython train.py --dataset {args.dataset} --lr {best['lr']} "
        f"--batch-size {best['batch_size']} --epochs {best['best_epoch']} --shuffle -o runs/{args.dataset}-optimized"
    )


if __name__ == "__main__":
    main()
