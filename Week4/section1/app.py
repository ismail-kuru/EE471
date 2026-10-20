from flask import Flask, jsonify, render_template, request

from custom_classes import Calculator

app = Flask(__name__)
calculator = Calculator()


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/calculate")
def calculate():
    """Calculate {"a": 10, "b": 5, "operation": "add"} and return {"result": 15}."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Request body must be a JSON object."), 400

    missing = [key for key in ("a", "b", "operation") if key not in data]
    if missing:
        return jsonify(error=f"Missing field(s): {', '.join(missing)}."), 400

    try:
        result = calculator.calculate(data["a"], data["b"], data["operation"])
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(result=result)


if __name__ == "__main__":
    # Port 5000 is taken by AirPlay Receiver on macOS.
    app.run(debug=True, port=5001)
