"""The website: sends an uploaded image to both Cog containers and returns both answers."""

import base64
import os
from concurrent.futures import ThreadPoolExecutor

import requests
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# The addresses of the Cog containers; docker-compose.yml sets them.
MODELS = {
    "fashion": {
        "baseline": os.getenv("FASHION_BASELINE_URL", "http://localhost:5003"),
        "optimized": os.getenv("FASHION_OPTIMIZED_URL", "http://localhost:5004"),
    },
    "cifar10": {
        "baseline": os.getenv("CIFAR10_BASELINE_URL", "http://localhost:5006"),
        "optimized": os.getenv("CIFAR10_OPTIMIZED_URL", "http://localhost:5007"),
    },
}
MODEL_TIMEOUT_SECONDS = 120

NOT_READY = "The model is not ready. Please try again in a few seconds."
NOT_AN_IMAGE = "This file could not be read as an image."


@app.errorhandler(ValueError)
def bad_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return jsonify(error="The image is too large (max 10 MB)."), 413


def ask_model(url, body):
    """Send the request to one Cog container; return its result, or {"error": ...}."""
    try:
        response = requests.post(f"{url}/predictions", json=body, timeout=MODEL_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException:
        return {"error": NOT_READY}
    prediction = response.json()
    if prediction.get("status") != "succeeded":
        return {"error": NOT_AN_IMAGE}
    return prediction["output"]


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/classify")
def classify():
    """Form fields: dataset and image (a file) → {"baseline": {...}, "optimized": {...}}."""
    models = MODELS.get(request.form.get("dataset"))
    if models is None:
        raise ValueError(f"dataset must be one of: {', '.join(MODELS)}.")
    image = request.files.get("image")
    if image is None or not image.filename:
        raise ValueError("Please choose an image first.")
    image_bytes = image.read()
    if not image_bytes:
        raise ValueError("The file is empty.")

    # Cog only accepts JSON, so the image travels as a base64 data URI.
    encoded = base64.b64encode(image_bytes).decode()
    body = {"input": {"image": f"data:{image.mimetype};base64,{encoded}"}}

    # Ask both models at the same time, so the page waits only for the slower one.
    with ThreadPoolExecutor() as executor:
        futures = {name: executor.submit(ask_model, url, body) for name, url in models.items()}
    results = {name: future.result() for name, future in futures.items()}

    # If no model could answer, it is one error. Otherwise, each side of the page shows its own result.
    errors = [result.get("error") for result in results.values()]
    if NOT_AN_IMAGE in errors and all(errors):
        raise ValueError(NOT_AN_IMAGE)
    if all(errors):
        return jsonify(error=NOT_READY), 503
    return jsonify(results)


if __name__ == "__main__":
    # Port 5000 is taken by AirPlay Receiver on macOS.
    app.run(debug=True, port=5001)
