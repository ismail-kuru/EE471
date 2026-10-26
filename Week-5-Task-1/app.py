from flask import Flask, Response, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

import speech

app = Flask(__name__)
# Reject uploads larger than 10 MB before they reach Azure.
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


@app.errorhandler(ValueError)
def bad_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return jsonify(error="Audio file is too large (max 10 MB)."), 413


@app.errorhandler(speech.NoSpeechError)
def no_speech(error):
    return jsonify(error=str(error)), 422


@app.errorhandler(speech.SpeechConfigError)
def not_configured(error):
    return jsonify(error=str(error)), 503


@app.errorhandler(speech.SpeechServiceError)
def azure_failed(error):
    return jsonify(error=str(error)), 502


@app.get("/")
def index():
    return render_template(
        "index.html",
        voices=speech.VOICES,
        default_voice=speech.DEFAULT_VOICE,
        languages=speech.LANGUAGES,
        default_language=speech.DEFAULT_LANGUAGE,
    )


@app.post("/api/tts")
def text_to_speech():
    """Body: {"text": "...", "voice": "en-US-JennyNeural"} → WAV audio."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    audio = speech.synthesize(data.get("text"), data.get("voice", speech.DEFAULT_VOICE))
    return Response(audio, mimetype="audio/wav")


@app.post("/api/stt")
def speech_to_text():
    """Form fields: audio (a WAV file) and language → {"text": "..."}."""
    audio = request.files.get("audio")
    if audio is None:
        raise ValueError("Please record or choose an audio file.")
    language = request.form.get("language", speech.DEFAULT_LANGUAGE)
    return jsonify(text=speech.transcribe(audio.read(), language))


if __name__ == "__main__":
    # Port 5000 is taken by AirPlay Receiver on macOS.
    app.run(debug=True, port=5001)
