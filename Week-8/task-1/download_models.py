"""Download the MediaPipe model used by each demo into models/.

Usage: python download_models.py
Models that are already there are skipped. The newer solutions (transcriber, text-to-speech,
decision maker, retriever, universal embedder, proofreader, summarizer, holistic) use larger
models from Hugging Face: about 1.3 GB together, most of it the speech transcriber.
"""

import urllib.request
from pathlib import Path

GOOGLE = "https://storage.googleapis.com/mediapipe-models"
HF = "https://huggingface.co/litert-community"
MODELS = {
    "yamnet.tflite": f"{GOOGLE}/audio_classifier/yamnet/float32/latest/yamnet.tflite",
    "language_detector.tflite": f"{GOOGLE}/language_detector/language_detector/float32/latest/language_detector.tflite",
    "bert_classifier.tflite": f"{GOOGLE}/text_classifier/bert_classifier/float32/latest/bert_classifier.tflite",
    "universal_sentence_encoder.tflite": f"{GOOGLE}/text_embedder/universal_sentence_encoder/float32/latest/universal_sentence_encoder.tflite",
    "blaze_face_short_range.tflite": f"{GOOGLE}/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite",
    "face_landmarker.task": f"{GOOGLE}/face_landmarker/face_landmarker/float16/latest/face_landmarker.task",
    "gesture_recognizer.task": f"{GOOGLE}/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task",
    "hand_landmarker.task": f"{GOOGLE}/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
    "efficientnet_lite0.tflite": f"{GOOGLE}/image_classifier/efficientnet_lite0/float32/latest/efficientnet_lite0.tflite",
    "mobilenet_v3_small.tflite": f"{GOOGLE}/image_embedder/mobilenet_v3_small/float32/latest/mobilenet_v3_small.tflite",
    "deeplab_v3.tflite": f"{GOOGLE}/image_segmenter/deeplab_v3/float32/latest/deeplab_v3.tflite",
    "interactive_segmentation.task": f"{HF}/MediaPipe-InteractiveSegmenter-MagicTouch/resolve/main/interactive_segmentation.task",
    "efficientdet_lite0.tflite": f"{GOOGLE}/object_detector/efficientdet_lite0/int8/latest/efficientdet_lite0.tflite",
    "pose_landmarker_full.task": f"{GOOGLE}/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task",
    # Newer solutions, hosted on Hugging Face.
    "holistic_landmarker.task": f"{HF}/MediaPipe-HolisticLandmarker/resolve/main/holistic_landmarker.task",
    "phonon_int8.litertlm": f"{HF}/phonon-31m-en/resolve/main/phonon_int8.litertlm",
    "proofread_quant_200m.litertlm": f"{HF}/MediaPipe-TextProofreader-200M/resolve/main/proofread_quant_200m.litertlm",
    "summarization_quant_200m_2modes.litertlm": f"{HF}/MediaPipe-TextSummarizer-200M/resolve/main/summarization_quant_200m_2modes.litertlm",
    # One embedding model shared by the Decision Maker, Semantic Retriever and Universal Embedder.
    "embeddinggemma-2-text-vision-440m.litertlm": f"{HF}/embeddinggemma-2-text-vision-440m-litert-lm/resolve/main/embeddinggemma-2-text-vision-440m.litertlm",
    "parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm": f"{HF}/parakeet-tdt-0.6b-v3/resolve/main/parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm",
}
MODELS_DIR = Path(__file__).resolve().parent / "models"


def main():
    MODELS_DIR.mkdir(exist_ok=True)
    for name, url in MODELS.items():
        target = MODELS_DIR / name
        if target.exists():
            print(f"skip  {name}")
            continue
        partial = target.with_suffix(target.suffix + ".part")  # So an interrupted download is not mistaken for a finished one.
        urllib.request.urlretrieve(url, partial)
        partial.rename(target)
        print(f"saved {name} ({target.stat().st_size / 1e6:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
