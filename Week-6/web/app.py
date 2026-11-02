"""The website: takes an uploaded image and asks the Cog container to classify it."""

import base64
import os

import requests
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# The address of the Cog container; docker-compose.yml sets it.
MODEL_URL = os.getenv("MODEL_URL", "http://localhost:5003")
MODEL_TIMEOUT_SECONDS = 120


class ModelError(Exception):
    """Raised when the Cog container cannot be reached."""


@app.errorhandler(ValueError)
def bad_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return jsonify(error="The image is too large (max 10 MB)."), 413


@app.errorhandler(ModelError)
def model_unavailable(error):
    return jsonify(error=str(error)), 503


def classify_image(image_bytes, mime_type):
    """Send the image to Cog's /predictions endpoint and return its JSON answer."""
    # Cog only accepts JSON, so the image travels as a base64 data URI.
    encoded = base64.b64encode(image_bytes).decode()
    body = {"input": {"image": f"data:{mime_type};base64,{encoded}"}}
    try:
        response = requests.post(f"{MODEL_URL}/predictions", json=body, timeout=MODEL_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException:
        raise ModelError("The model is not ready. Please try again in a few seconds.")
    return response.json()


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/classify")
def classify():
    """Form field: image (a file) → the predicted class and the most likely cat kinds."""
    image = request.files.get("image")
    if image is None or not image.filename:
        raise ValueError("Please choose an image first.")
    image_bytes = image.read()
    if not image_bytes:
        raise ValueError("The file is empty.")

    prediction = classify_image(image_bytes, image.mimetype)
    if prediction.get("status") != "succeeded":
        raise ValueError("This file could not be read as an image.")
    return jsonify(prediction["output"])


if __name__ == "__main__":
    # Port 5000 is taken by AirPlay Receiver on macOS.
    app.run(debug=True, port=5001)
