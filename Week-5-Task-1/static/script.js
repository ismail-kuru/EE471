// One page, two tabs: text to speech and speech to text. Azure work happens in Flask;
// this file handles the page and, for speech to text, converts audio to WAV.

// --- Shared helpers ---

function showStatus(element, kind, message) {
  element.className = `status ${kind}`;
  element.textContent = message;
  element.hidden = false;
}

// Turns a failed fetch response into the API's error message.
async function errorMessage(response) {
  try {
    const data = await response.json();
    return data.error || `Request failed (${response.status}).`;
  } catch {
    return `Request failed (${response.status}).`;
  }
}

// --- Tabs ---

const tabs = document.querySelectorAll(".tab");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((other) => {
      const active = other === tab;
      other.classList.toggle("active", active);
      other.setAttribute("aria-selected", String(active));
      document.getElementById(other.dataset.panel).hidden = !active;
    });
  });
});

// --- Text to speech: send the text to Flask, which asks Azure for a WAV file ---

const ttsText = document.getElementById("tts-text");
const ttsVoice = document.getElementById("tts-voice");
const ttsButton = document.getElementById("tts-synthesize");
const ttsStatus = document.getElementById("tts-status");
const ttsResult = document.getElementById("tts-result");
const ttsAudio = document.getElementById("tts-audio");
const ttsDownload = document.getElementById("tts-download");

let audioUrl = null;

async function synthesize() {
  ttsButton.disabled = true;
  showStatus(ttsStatus, "working", "Synthesizing…");
  try {
    const response = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: ttsText.value, voice: ttsVoice.value }),
    });
    if (!response.ok) {
      throw new Error(await errorMessage(response));
    }
    const audio = await response.blob();
    // Free the previous audio's memory before making a new URL.
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    audioUrl = URL.createObjectURL(audio);
    ttsAudio.src = audioUrl;
    ttsDownload.href = audioUrl;
    ttsResult.hidden = false;
    showStatus(ttsStatus, "success", "✓ Speech synthesized successfully!");
  } catch (error) {
    showStatus(ttsStatus, "error", error.message);
  } finally {
    ttsButton.disabled = false;
  }
}

function clearTts() {
  ttsText.value = "";
  ttsStatus.hidden = true;
  ttsResult.hidden = true;
  ttsAudio.removeAttribute("src");
}

ttsButton.addEventListener("click", synthesize);
document.getElementById("tts-clear").addEventListener("click", clearTts);

// --- Speech to text: record or pick a file, convert it to WAV, and send it to Flask ---

const sttStart = document.getElementById("stt-start");
const sttStop = document.getElementById("stt-stop");
const sttFile = document.getElementById("stt-file");
const sttLanguage = document.getElementById("stt-language");
const sttRecording = document.getElementById("stt-recording");
const sttPreview = document.getElementById("stt-preview");
const sttTranscribe = document.getElementById("stt-transcribe");
const sttResult = document.getElementById("stt-result");
const sttText = document.getElementById("stt-text");
const sttStatus = document.getElementById("stt-status");

// Azure's Python SDK reads 16-bit PCM WAV; 16 kHz mono is what speech recognition expects.
const TARGET_SAMPLE_RATE = 16000;

let recorder = null;
let recordedBlob = null;

// Any format the browser can play → 16 kHz mono 16-bit WAV.
async function toWav(blob) {
  const context = new AudioContext();
  let decoded;
  try {
    decoded = await context.decodeAudioData(await blob.arrayBuffer());
  } catch {
    throw new Error("This audio format could not be read. Try a WAV or MP3 file.");
  } finally {
    context.close();
  }
  // An OfflineAudioContext with 1 channel at 16 kHz mixes down and resamples for us.
  const length = Math.ceil(decoded.duration * TARGET_SAMPLE_RATE);
  const offline = new OfflineAudioContext(1, length, TARGET_SAMPLE_RATE);
  const source = offline.createBufferSource();
  source.buffer = decoded;
  source.connect(offline.destination);
  source.start();
  const rendered = await offline.startRendering();
  return encodeWav(rendered.getChannelData(0), TARGET_SAMPLE_RATE);
}

function encodeWav(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeText = (offset, text) => [...text].forEach((c, i) => view.setUint8(offset + i, c.charCodeAt(0)));

  writeText(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeText(8, "WAVE");
  writeText(12, "fmt ");
  view.setUint32(16, 16, true);            // fmt chunk size
  view.setUint16(20, 1, true);             // PCM
  view.setUint16(22, 1, true);             // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true); // byte rate
  view.setUint16(32, 2, true);             // block align
  view.setUint16(34, 16, true);            // bits per sample
  writeText(36, "data");
  view.setUint32(40, samples.length * 2, true);

  samples.forEach((sample, i) => {
    const clipped = Math.max(-1, Math.min(1, sample));
    view.setInt16(44 + i * 2, clipped < 0 ? clipped * 0x8000 : clipped * 0x7fff, true);
  });
  return new Blob([view], { type: "audio/wav" });
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const chunks = [];
    recorder = new MediaRecorder(stream);
    recorder.addEventListener("dataavailable", (event) => chunks.push(event.data));
    recorder.addEventListener("stop", () => {
      // Turn the microphone off as soon as recording ends.
      stream.getTracks().forEach((track) => track.stop());
      recordedBlob = new Blob(chunks, { type: recorder.mimeType });
      sttPreview.src = URL.createObjectURL(recordedBlob);
      sttPreview.hidden = false;
    });
    recorder.start();
    sttFile.value = "";
    sttStart.disabled = true;
    sttStop.disabled = false;
    sttRecording.hidden = false;
    sttStatus.hidden = true;
  } catch {
    showStatus(sttStatus, "error", "Microphone access was denied or is not available.");
  }
}

function stopRecording() {
  recorder.stop();
  sttStart.disabled = false;
  sttStop.disabled = true;
  sttRecording.hidden = true;
}

async function transcribe() {
  // A newly chosen file wins over an older recording.
  const source = sttFile.files[0] || recordedBlob;
  if (!source) {
    showStatus(sttStatus, "error", "Please record or choose an audio file first.");
    return;
  }
  sttTranscribe.disabled = true;
  showStatus(sttStatus, "working", "Transcribing…");
  try {
    const form = new FormData();
    form.append("audio", await toWav(source), "audio.wav");
    form.append("language", sttLanguage.value);
    const response = await fetch("/api/stt", { method: "POST", body: form });
    if (!response.ok) {
      throw new Error(await errorMessage(response));
    }
    const data = await response.json();
    sttText.textContent = data.text;
    sttResult.hidden = false;
    showStatus(sttStatus, "success", "✓ Audio transcribed successfully!");
  } catch (error) {
    showStatus(sttStatus, "error", error.message);
  } finally {
    sttTranscribe.disabled = false;
  }
}

function clearStt() {
  recordedBlob = null;
  sttFile.value = "";
  sttPreview.hidden = true;
  sttPreview.removeAttribute("src");
  sttResult.hidden = true;
  sttStatus.hidden = true;
}

async function copyText() {
  try {
    await navigator.clipboard.writeText(sttText.textContent);
    showStatus(sttStatus, "success", "✓ Text copied to clipboard.");
  } catch {
    showStatus(sttStatus, "error", "Could not copy the text.");
  }
}

sttStart.addEventListener("click", startRecording);
sttStop.addEventListener("click", stopRecording);
sttTranscribe.addEventListener("click", transcribe);
document.getElementById("stt-clear").addEventListener("click", clearStt);
document.getElementById("stt-copy").addEventListener("click", copyText);
sttFile.addEventListener("change", () => {
  // Show the chosen file in the player so the user can check it before transcribing.
  if (sttFile.files[0]) {
    sttPreview.src = URL.createObjectURL(sttFile.files[0]);
    sttPreview.hidden = false;
  }
});
