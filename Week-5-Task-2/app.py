from flask import Flask, Response, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

import commands
import speech
from custom_classes import Calculator

app = Flask(__name__)
# A spoken command is a few seconds long; reject anything over 5 MB.
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
calculator = Calculator()


@app.errorhandler(ValueError)
def bad_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return jsonify(error="Recording is too long (max 5 MB)."), 413


@app.errorhandler(speech.NoSpeechError)
def no_speech(error):
    return jsonify(error=str(error)), 422


@app.errorhandler(speech.SpeechConfigError)
def not_configured(error):
    return jsonify(error=str(error)), 503


@app.errorhandler(speech.SpeechServiceError)
def azure_failed(error):
    return jsonify(error=str(error)), 502


def json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


@app.get("/")
def index():
    return render_template("index.html", key_words=commands.KEY_WORDS)


@app.post("/api/calculate")
def calculate():
    """Calculate {"a": 10, "b": 5, "operation": "add"} and return {"result": 15}."""
    data = json_body()
    missing = [key for key in ("a", "b", "operation") if key not in data]
    if missing:
        raise ValueError(f"Missing field(s): {', '.join(missing)}.")
    return jsonify(result=calculator.calculate(data["a"], data["b"], data["operation"]))


@app.post("/api/speak")
def speak():
    """Body: {"text": "three"} → WAV audio of the text read aloud."""
    return Response(speech.speak(json_body().get("text")), mimetype="audio/wav")


@app.post("/api/voice")
def voice_command():
    """Form field: audio (WAV) → {"heard": "five plus two is", "keys": ["5", "+", "2", "="]}."""
    audio = request.files.get("audio")
    if audio is None:
        raise ValueError("No audio was recorded.")
    heard = speech.listen(audio.read())
    keys = commands.parse(heard)
    if not keys:
        raise speech.NoSpeechError(f"I heard “{heard}”, but no calculator commands.")
    return jsonify(heard=heard, keys=keys)


if __name__ == "__main__":
    # Port 5000 is taken by AirPlay Receiver on macOS.
    app.run(debug=True, port=5001)
