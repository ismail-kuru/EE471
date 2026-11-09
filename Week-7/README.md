# Week 7: Image Classifiers with PyTorch and Cog

Two classifiers trained with PyTorch: a garment classifier (FashionMNIST) and a CIFAR10 classifier.
Each one has a previous model and a model improved by hyperparameter optimization. A website
compares the two side by side. Every model runs in its own Cog container.

| | Previous model | Optimized model |
|---|---|---|
| **FashionMNIST** test accuracy | 64.9% | **87.9%** |
| **CIFAR10** test accuracy | 52.2% | **62.9%** |

See [`report.docx`](report.docx) for the analysis.

## Run the website

Docker Desktop must be running and [Cog](https://github.com/replicate/cog) must be installed
(`brew install replicate/tap/cog`). The trained weights are in `model/weights`, so no training is needed.

```bash
cd Week-7/model
cog build -t week7-classifier    # the model image
cd ..
docker compose up --build        # build the website and start all containers
```

Open http://localhost:5005, choose **Garments** or **CIFAR10**, upload an image and click
**Classify**. Press `Ctrl+C` to stop.

| Address | What runs there |
|---|---|
| http://localhost:5005 | The website |
| http://localhost:5003 | FashionMNIST previous model (Cog API) |
| http://localhost:5004 | FashionMNIST optimized model (Cog API) |
| http://localhost:5006 | CIFAR10 previous model (Cog API) |
| http://localhost:5007 | CIFAR10 optimized model (Cog API) |

The models expect images like their training data, so test images work best. To create some, set up
the training environment below and run:

```bash
.venv/bin/python export_samples.py fashion
.venv/bin/python export_samples.py cifar10
```

The images are saved in `samples/`.

## Live prediction logs from inside a container

```bash
docker exec -it cifar10-optimized sh
tail -f /tmp/predictions.log
```

## API check with Postman

Cog's API only accepts JSON, so the image is sent inside the JSON as base64. First create a request file:

```bash
python3 make_postman_body.py samples/cifar10/ship-1.png      # writes ship-1-request.json next to the image
```

In Postman:

1. Choose `POST` and enter `http://localhost:5007/predictions`.
2. In **Headers**, add `Content-Type: application/json`.
3. In **Body**, choose **binary** and select the request file.
4. Click **Send**. The answer's `output` holds `predicted_class`.

## Train the models

Training runs on your computer, not in a container. The commands below reproduce the four models.

```bash
cd Week-7
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# The previous models: the settings of the PyTorch tutorials.
.venv/bin/python train.py --dataset fashion --lr 0.001 --batch-size 64 --epochs 5 -o runs/fashion-baseline
.venv/bin/python train.py --dataset cifar10 --lr 0.001 --momentum 0.9 --batch-size 4 --epochs 2 --shuffle -o runs/cifar10-baseline

# Search for good hyperparameters. Each search prints the command that trains its best model.
.venv/bin/python tune.py --dataset fashion -o tuning/fashion.json
.venv/bin/python tune.py --dataset cifar10 -o tuning/cifar10.json

# The optimized models.
.venv/bin/python train.py --dataset fashion --lr 0.1 --batch-size 32 --epochs 10 --shuffle -o runs/fashion-optimized
.venv/bin/python train.py --dataset cifar10 --lr 0.003 --momentum 0.9 --batch-size 32 --epochs 10 --shuffle -o runs/cifar10-optimized
```

To serve a new model, copy its `model.pth` and `metrics.json` to `model/weights/<model name>.pth` and
`.json`, then build the image again. Results can differ slightly between computers.

## How the hyperparameter search works

`tune.py` tries every combination of the values listed in `model/models.py` (a grid search). Each one
is scored on 10,000 images held out of the training set. The test images are not used, so the final
test accuracy stays a fair measure. The best settings are then used to train on the full training set.

## Files

| File | Role |
|---|---|
| `train.py` | Trains one model on either dataset, using command-line options. |
| `tune.py` | The hyperparameter search. |
| `model/models.py` | The two networks and the settings of each dataset. |
| `model/run.py` | Loads a model chosen by `MODEL_NAME` and answers predictions; writes the log. |
| `model/cog.yaml` | Tells Cog how to build the model image. |
| `model/weights/` | The four trained models and their results. |
| `tuning/` | The results of each hyperparameter search. |
| `web/` | The website and its `Dockerfile`. |
| `docker-compose.yml` | Starts the four model containers and the website. |
| `export_samples.py` | Saves test images to try on the website. |
| `make_postman_body.py` | Creates the JSON request file for Postman. |
| `report.docx` | The performance report. |
