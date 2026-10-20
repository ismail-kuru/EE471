# Week 4 – Calculator and Library App

## Section 1: Calculator

Starting point: the `Calculator` class from Mini Project 1
([EE471_MP1_Calculator](https://github.com/ismail-kuru/EE471_MP1_Calculator)).

### Part 1: Figma design

- Figma (view only): https://www.figma.com/design/ChzHau46mB9TC91yU8ktHM/Untitled?node-id=1-3

![Calculator design](design/calculator.png)

### Part 2: Web calculator with a Flask backend

Code is in [`section1/`](section1/). All arithmetic runs in Python; the page never
uses `eval()` and does no math itself.

```bash
cd Week4
python3 -m venv .venv
.venv/bin/pip install -r section1/requirements.txt
cd section1
../.venv/bin/python app.py      # http://127.0.0.1:5001
```

`POST /api/calculate`

| | Body | Status |
|---|---|---|
| Request | `{"a": 10, "b": 5, "operation": "add"}` | |
| Success | `{"result": 15}` | 200 |
| Error | `{"error": "Cannot divide by zero."}` | 400 |

`operation` is one of `add`, `subtract`, `multiply`, `divide`. Invalid JSON, missing
fields, non-numeric operands, unknown operations and division by zero return 400.

```bash
curl -X POST http://127.0.0.1:5001/api/calculate \
     -H "Content-Type: application/json" \
     -d '{"a": 10, "b": 5, "operation": "add"}'
```

Prompts and corrections: [`section1/PROMPTS.md`](section1/PROMPTS.md).

## Section 2: Library App

Starting point: `custom_classes.py` and `main.py` from the merged Week 3 `main` branch.
Code is in [`section2/`](section2/).

### Part 2: CRUD methods

`custom_classes.py` adds `ItemNotFoundError` and `ItemStateError`, unique ids that are
never reused, `to_dict()`, and `get_item`, `list_items`, `update_item` and `remove_item`
on `LibraryCollection`. Run `python3 main.py` inside `section2/` to see every method
and every exception.

### Part 3: Flask REST API

```bash
cd Week4/section2
../.venv/bin/pip install -r requirements.txt
../.venv/bin/python app.py      # http://127.0.0.1:5001
```

| Endpoint | Purpose | Success | Errors |
|---|---|---|---|
| `POST /api/items` | Create a book or DVD | 201 + item | 400 |
| `GET /api/items` | List items, `?available=true`, `?type=book` | 200 | 400 bad filter |
| `GET /api/items/<id>` | Get one item | 200 | 404 |
| `PUT /api/items/<id>` | Replace all editable fields | 200 | 400, 404 |
| `PATCH /api/items/<id>` | Change some editable fields | 200 | 400, 404 |
| `DELETE /api/items/<id>` | Remove an item | 204 | 404, 409 if checked out |
| `POST /api/items/<id>/checkout` | Check an item out | 200 | 404, 409 already out |
| `POST /api/items/<id>/return` | Return an item | 200 | 404, 409 not checked out |

Every response is JSON; errors look like `{"error": "<message>"}`. `app.py` only
translates HTTP to `LibraryCollection` calls and maps exceptions to status codes
(`ValueError` → 400, `ItemNotFoundError` → 404, `ItemStateError` → 409).

Example item:

```json
{"id": 3, "type": "dvd", "title": "Arrival", "author": "Denis Villeneuve", "duration": 116, "is_available": false}
```

### Part 4: Frontend

Flask serves the page at <http://127.0.0.1:5001> (`templates/index.html`,
`static/style.css`, `static/script.js`). The layout follows the example screenshot in the
exercise. The page only calls the API: filters are sent as query parameters, and API
error messages (for example 409 when deleting a checked-out item) appear in the error
area at the top.

Prompts and corrections: [`section2/PROMPTS.md`](section2/PROMPTS.md).
