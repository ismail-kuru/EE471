from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from custom_classes import DVD, Book, ItemNotFoundError, ItemStateError, LibraryCollection

app = Flask(__name__)

library = LibraryCollection()
library.add_item(Book("The Great Gatsby", "F. Scott Fitzgerald", 180))
library.add_item(DVD("Inception", "Christopher Nolan", 148))
library.add_item(Book("1984", "George Orwell", 328))
library.add_item(DVD("Arrival", "Denis Villeneuve", 116))


# --- Errors: every rule lives in custom_classes.py; here we only pick the status code.

@app.errorhandler(ItemNotFoundError)
def not_found(error):
    return jsonify(error=str(error)), 404


@app.errorhandler(ItemStateError)
def conflict(error):
    return jsonify(error=str(error)), 409


@app.errorhandler(ValueError)
def bad_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(HTTPException)
def http_error(error):
    # Flask's own errors (unknown URL, wrong method) are HTML by default; keep the API all-JSON.
    return jsonify(error=error.description), error.code


def json_body():
    """Return the request body as a dict, or raise ValueError if it is not a JSON object."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


def bool_query_param(name):
    """Turn ?name=true/false into True/False; None if absent; ValueError otherwise."""
    value = request.args.get(name)
    if value is None:
        return None
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    raise ValueError(f"{name} must be true or false.")


# --- Routes: translate HTTP to LibraryCollection method calls.

@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/items")
def create_item():
    data = json_body()
    item_type = data.pop("type", None)
    item = library.create_item(item_type, **data)
    return jsonify(item.to_dict()), 201, {"Location": f"/api/items/{item.id}"}


@app.get("/api/items")
def list_items():
    items = library.list_items(
        available=bool_query_param("available"),
        item_type=request.args.get("type"),
    )
    return jsonify([item.to_dict() for item in items])


@app.get("/api/items/<int:item_id>")
def get_item(item_id):
    return jsonify(library.get_item(item_id).to_dict())


@app.put("/api/items/<int:item_id>")
def replace_item(item_id):
    return jsonify(library.replace_item(item_id, **json_body()).to_dict())


@app.patch("/api/items/<int:item_id>")
def update_item(item_id):
    return jsonify(library.update_item(item_id, **json_body()).to_dict())


@app.delete("/api/items/<int:item_id>")
def remove_item(item_id):
    library.remove_item(item_id)
    return "", 204


@app.post("/api/items/<int:item_id>/checkout")
def checkout_item(item_id):
    item = library.get_item(item_id)
    message = item.checkout()
    return jsonify(message=message, item=item.to_dict())


@app.post("/api/items/<int:item_id>/return")
def return_item(item_id):
    item = library.get_item(item_id)
    message = item.return_item()
    return jsonify(message=message, item=item.to_dict())


if __name__ == "__main__":
    # Port 5000 is taken by AirPlay Receiver on macOS.
    app.run(debug=True, port=5001)
