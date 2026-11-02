# EE471 – Modern Software Development Practices and Technologies

Coursework for EE 471 at Izmir Institute of Technology (Fall 2026).

## Repository layout

Each week and each project lives in its own folder. The apps have their own `README.md`
with setup instructions and their own `requirements.txt`.

| Folder | Topic | Status |
|---|---|---|
| [`week01-conform/`](week01-conform/) | Brain teaser: *You Will All Conform* | Done |
| [`Week4/`](Week4/) | Flask web apps: calculator (Section 1) and library REST API with a frontend (Section 2) | Done |
| [`week05-azure-speech/`](week05-azure-speech/) | Azure AI Speech: text-to-speech and speech-to-text (Flask) | From previous term |
| [`Week-5-Task-1/`](Week-5-Task-1/) | Azure Speech Studio: text to speech, speech to text, diarization, translation and pronunciation assessment; containerized in Week 6 | Done |
| [`Week-5-Task-2/`](Week-5-Task-2/) | Voice-activated calculator with Azure Speech; containerized in Week 6 | Done |
| [`Mini-Project-2/`](Mini-Project-2/) | Voice-activated Library App: every library endpoint by voice, with spoken replies and errors | Done |
| [`Week-6/`](Week-6/) | Docker and Cog: cat-kind classifier website using a pre-trained ResNet-50 model | Done |

## Workflow

- `main` always holds finished, working code.
- Each piece of work is done on its own branch and merged into `main` through a pull
  request.
- Secrets such as Azure keys go in a local `.env` file, which is never committed.
  Each project that needs one ships a `.env.example`.

## Archive

Work from the previous term is preserved in the `archive-2025-26` tag.
