# Task 1: MediaPipe Solutions in Python

One short Python script for each of the 22 [MediaPipe solutions](https://ai.google.dev/edge/mediapipe/solutions/guide).
Each script loads its model, runs it on a sample from `samples/`, prints the result and, for the
image tasks, saves an annotated picture to `outputs/`. Most scripts also accept your own input:
`python face_detector.py my-photo.jpg`, `python text_proofreader.py "Some text with erors."`.

## Setup

Task 1 has its own virtual environment, because the newer solutions need MediaPipe 1.2
(Tasks 2 and 3 use `Week-8/.venv` with MediaPipe 0.10, the version their Cog images pin).

```bash
cd Week-8/task-1
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python download_models.py     # about 1.5 GB of models into models/ (not committed)
.venv/bin/python face_detector.py
```

## The demos

### Vision

| Solution | Script | Sample | Result on the sample |
|---|---|---|---|
| Face Detector | `face_detector.py` | `face-3.png` | 1 face, 94%, with 6 key points |
| Face Landmarker | `face_landmarker.py` | `face-3.png` | 478 points and 52 expression scores |
| Gesture Recognizer | `gesture_recognizer.py` | 3 hand photos | Thumb_Up 73%, Victory 91%, Pointing_Up 82% |
| Hand Landmarker | `hand_landmarker.py` | `woman_hands.jpg` | 2 hands, 21 points each, left and right |
| Holistic Landmarker | `holistic_landmarker.py` | `pose-1.jpg` | pose 33, face 478, each hand 21 points, in one call |
| Image Classifier | `image_classifier.py` | `cat.jpg` | tiger cat 45%, tabby 38% |
| Image Embedder | `image_embedder.py` | 3 images | cat vs. cat and dog: 0.14; cat vs. hand: 0.00 |
| Image Segmenter | `image_segmenter.py` | `cat_and_dog.jpg` | dog, 33% of the pixels |
| Interactive Segmenter | `interactive_segmenter.py` | `cat_and_dog.jpg` + a point on the dog | the dog, 20% of the pixels |
| Object Detector | `object_detector.py` | `cat_and_dog.jpg` | dog 89%, cat 82%, with boxes |
| Pose Landmarker | `pose_landmarker.py` | `pose-1.jpg` | 33 body points |

### Audio

| Solution | Script | Sample | Result on the sample |
|---|---|---|---|
| Audio Classifier | `audio_classifier.py` | `speech.wav`, `tone.wav` | Speech 94–100%; the tone: Sine wave 89% |
| Audio Transcriber | `audio_transcriber.py` | `speech.wav`, `outputs/text_to_speech.wav` | the speech as text, with punctuation |
| Text-to-Speech | `text_to_speech.py` | a sentence | `outputs/text_to_speech.wav`, 24 kHz; transcribing it gives the sentence back |

### Text and language

| Solution | Script | Sample | Result on the sample |
|---|---|---|---|
| Language Detector | `language_detector.py` | 4 sentences | en, tr, fr, de, all 99–100% |
| Text Classifier | `text_classifier.py` | 3 movie reviews | positive / negative (100%), "okay" review: negative 78% |
| Text Embedder | `text_embedder.py` | 3 sentences | the two football sentences: 0.92; vs. the stock market one: 0.68–0.70 |
| Text Proofreader | `text_proofreader.py` | 3 sentences with mistakes | "Their are severel typos..." → "There are several typos..." |
| Text Summarizer | `text_summarizer.py` | a 118-word paragraph | a 1–2 sentence TLDR and 5 key points |

### Decisions and retrieval

| Solution | Script | Sample | Result on the sample |
|---|---|---|---|
| Decision Maker | `decision_maker.py` | 3 support messages | the right category (94–100%) and complaint yes / no |
| Universal Embedder | `universal_embedder.py` | 3 sentences + 3 photos | each sentence is closest to its matching photo |
| Semantic Retriever | `semantic_retriever.py` | 5 stored facts + 3 questions | the fact that answers each question comes first |

Things worth knowing:

- **Classifier vs. detector vs. segmenter:** the Image Classifier gives one label for the whole image,
  the Object Detector a box per object, and the Image Segmenter a class for every pixel.
- **Embeddings** are compared with cosine similarity. Only the differences matter: the Universal
  Sentence Encoder gives unrelated sentences around 0.7, while MobileNet gives unrelated images
  around 0. The Universal Embedder puts texts and images in the same space, so a sentence can be
  compared with a photo.
- **The language solutions run on the computer:** transcription, speech, proofreading and
  summarizing need no internet service once the models are downloaded.
- **Decision Maker's yes / no threshold** is lowered to 0.25, because this small model gives
  complaints about 30% "yes" and plain questions about 10%.

## Models

| Model | Used by | Size |
|---|---|---|
| Parakeet TDT 0.6B | Audio Transcriber | 615 MB |
| EmbeddingGemma 2 (440M) | Decision Maker, Universal Embedder, Semantic Retriever | 388 MB |
| Proofread 200M | Text Proofreader | 118 MB |
| Summarization 200M | Text Summarizer | 118 MB |
| Phonon 31M | Text-to-Speech | 87 MB |
| The 15 other models | the remaining solutions | about 130 MB |

## Files

| File | Role |
|---|---|
| `*.py` (one per solution) | The demos. |
| `common.py` | Shared helpers: model paths, loading images, drawing and saving results. |
| `download_models.py` | Downloads every model into `models/` (not committed). |
| `requirements.txt` | MediaPipe 1.2.3, which also installs OpenCV and NumPy. |
| `samples/` | Inputs: images from MediaPipe's examples and the course, audio made with macOS `say`. |
| `outputs/` | The annotated pictures and the generated speech. |
