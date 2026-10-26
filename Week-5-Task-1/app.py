from flask import Flask, Response, jsonify, render_template, request

import speech

app = Flask(__name__)


@app.errorhandler(ValueError)
def bad_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(speech.SpeechConfigError)
def not_configured(error):
    return jsonify(error=str(error)), 503


@app.errorhandler(speech.SpeechServiceError)
def azure_failed(error):
    return jsonify(error=str(error)), 502


@app.get("/")
def index():
    return render_template("index.html", voices=speech.VOICES, default_voice=speech.DEFAULT_VOICE)


@app.post("/api/tts")
def text_to_speech():
    """Body: {"text": "...", "voice": "en-US-JennyNeural"} → WAV audio."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    audio = speech.synthesize(data.get("text"), data.get("voice", speech.DEFAULT_VOICE))
    return Response(audio, mimetype="audio/wav")


if __name__ == "__main__":
    # Port 5000 is taken by AirPlay Receiver on macOS.
    app.run(debug=True, port=5001)
