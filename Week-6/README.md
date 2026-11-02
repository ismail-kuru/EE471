# Week 6: Docker and Cog

## Task 1: Containerized apps

The Dockerfiles and run commands are next to the apps:

- Speech Studio: [`Week-5-Task-1`](../Week-5-Task-1/README.md#run-with-docker)
- Voice calculator: [`Week-5-Task-2`](../Week-5-Task-2/README.md#run-with-docker)

## Task 2: Cat-kind classifier

Upload a photo of a cat, click **Classify**, and the site shows what kind of cat it is.

| Container | Role | Address |
|---|---|---|
| `cat-web` | Flask website, built from `web/Dockerfile` | http://localhost:5005 |
| `cat-model` | Cog's pre-trained ResNet-50 behind an HTTP API, built from `model/cog.yaml` | http://localhost:5003 |

The model knows 1000 ImageNet classes. `model/run.py` treats 13 of them as kinds of cat:
tabby, tiger cat, Persian cat, Siamese cat, Egyptian cat, cougar, lynx, leopard, snow
leopard, jaguar, lion, tiger and cheetah. If these together get less than 50%, the image
counts as "not a cat", and the site shows the class the model picked instead.

### Setup

Docker Desktop must be running and [Cog](https://github.com/replicate/cog) must be installed
(`brew install replicate/tap/cog`).

```bash
cd Week-6/model
cog build -t cat-classifier-model      # the model image
cd ..
docker compose up --build              # build the website and start both containers
```

Open http://localhost:5005. Press `Ctrl+C` to stop.

### Live prediction logs from inside the container

In a second terminal:

```bash
docker exec -it cat-model sh           # open a shell inside the running container
tail -f /tmp/predictions.log           # follow the log, then classify an image on the site
```

### API check with Postman

Cog's API only accepts JSON (other content types get `415`), so the image is sent inside
the JSON as base64. First turn an image into a request file:

```bash
python3 make_postman_body.py /path/to/cat.jpg      # writes cat-request.json next to the image
```

In Postman:

1. Choose `POST` and enter `http://localhost:5003/predictions`.
2. In **Headers**, add `Content-Type: application/json`.
3. In **Body**, choose **binary** and select `cat-request.json`.
4. Click **Send**.

The answer's `output` holds the predicted class:

```json
{
  "status": "succeeded",
  "output": {
    "predicted_class": "tiger cat",
    "confidence": 0.4597,
    "is_cat": true,
    "top_kinds": [
      {"kind": "tiger cat", "probability": 0.4597},
      {"kind": "Egyptian cat", "probability": 0.3693},
      {"kind": "tabby", "probability": 0.1658}
    ]
  }
}
```

### Files

| File | Role |
|---|---|
| `model/cog.yaml` | Tells Cog the Python version and packages, stores the weights in the image, and names the runner class. |
| `model/run.py` | Loads the model in `setup()`, classifies an image in `run()`, and writes the prediction log. |
| `web/Dockerfile` | Builds the website's image. |
| `web/app.py` | Serves the page and forwards uploads to Cog as `POST /predictions`. |
| `web/static/script.js` | Shows the image preview and the result. |
| `docker-compose.yml` | Starts both containers and connects the website to the model. |
| `make_postman_body.py` | Creates the JSON request file for Postman. |
