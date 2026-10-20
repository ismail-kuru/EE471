# PROMPTS – Section 1

## Tools

- **Claude app** – help with Auto Layout in Figma (Part 1).
- **Claude Code** (Claude Opus 5.5) – web page and Flask backend (Part 2).

## Main prompts

### 1. Auto Layout (Claude app)

I designed the calculator in Figma myself but could not get Auto Layout to work, so I
asked Claude:

> I designed this calculator in Figma: a blue frame, a white display on top and a 4×4
> grid of buttons (7 8 9 ÷ / 4 5 6 × / 1 2 3 − / 0 . = +). I couldn't set up Auto Layout.
> How should I structure the frames so the rows and the display use Auto Layout?

### 2. Web page + Flask backend (Claude Code)

> Here is my Figma design (`design/calculator.png`) and the Week 4 exercise PDF.
> Turn the design into a working web page with HTML, CSS and JavaScript. All
> calculations must run on a Flask server on localhost: Flask serves the page and
> exposes `POST /api/calculate` with JSON. Don't use `eval()`. Return an error message
> for invalid input and for division by zero. Reuse my `Calculator` class from Mini
> Project 1.

## Corrections

| # | What I noticed | What I changed / asked for |
|---|---|---|
| 1 | The first CSS copied the square example from the PDF, not my design (rounded frame, rounded display, oval buttons). | Asked it to match my PNG exactly; colors and sizes are now measured from `design/calculator.png`. |
| 2 | The PDF says "using the JSON format given above", but no format is given. | Settled on `{"a": 10, "b": 5, "operation": "add"}` → `{"result": 15}`, errors as `{"error": "..."}` with status 400. |
| 3 | Port 5000 is already used on macOS (AirPlay Receiver). | The app runs on port 5001. |
| 4 | Testing with curl, `{"a": NaN, ...}` and `1e308 * 10` returned **200** with `NaN` / `Infinity`, which is not valid JSON, so the page could not read it. | `Calculator.calculate()` now rejects non-finite numbers and results with a 400 error. |
| 5 | After clicking a key, pressing **Enter** ran `=` **and** clicked the focused button again (e.g. repeated the last `+`). | Handled keys now call `event.preventDefault()`. |
| 6 | Python treats `True`/`False` as numbers, so `{"a": true}` was calculated as 1. | Booleans are rejected in `calculate()`. |

## How the code is split

- `custom_classes.py` – all rules: the four operations, input checks, division by zero.
- `app.py` – only translates HTTP ↔ `Calculator.calculate()` and serves the page.
- `static/script.js` – only tracks key presses and calls the API; it does no arithmetic.
