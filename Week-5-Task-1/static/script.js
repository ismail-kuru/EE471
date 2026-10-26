// One page, five tabs. Azure work happens in Flask; this file handles the page and,
// for every audio feature, converts recordings and uploads to WAV first.

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

// POSTs form data and returns the response, or throws the API's error message.
async function postForm(url, form) {
  const response = await fetch(url, { method: "POST", body: form });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response;
}

// Runs an async action with its button disabled and a status line kept up to date.
async function withStatus(button, status, workingText, action) {
  button.disabled = true;
  showStatus(status, "working", workingText);
  try {
    const successText = await action();
    showStatus(status, "success", successText);
  } catch (error) {
    showStatus(status, "error", error.message);
  } finally {
    button.disabled = false;
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

// --- Audio: any format the browser can play → 16 kHz mono 16-bit WAV ---

// Azure's Python SDK reads 16-bit PCM WAV; 16 kHz mono is what speech recognition expects.
const TARGET_SAMPLE_RATE = 16000;

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

// The record/upload controls of one tab (see the audio_input macro in index.html).
class AudioInput {
  constructor(prefix, status) {
    this.status = status;
    this.startButton = document.getElementById(`${prefix}-start`);
    this.stopButton = document.getElementById(`${prefix}-stop`);
    this.fileInput = document.getElementById(`${prefix}-file`);
    this.recordingNote = document.getElementById(`${prefix}-recording`);
    this.preview = document.getElementById(`${prefix}-preview`);
    this.recorder = null;
    this.recordedBlob = null;

    this.startButton.addEventListener("click", () => this.start());
    this.stopButton.addEventListener("click", () => this.stop());
    this.fileInput.addEventListener("change", () => {
      // Show the chosen file in the player so the user can check it first.
      if (this.fileInput.files[0]) this.showPreview(this.fileInput.files[0]);
    });
  }

  showPreview(blob) {
    this.preview.src = URL.createObjectURL(blob);
    this.preview.hidden = false;
  }

  async start() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks = [];
      this.recorder = new MediaRecorder(stream);
      this.recorder.addEventListener("dataavailable", (event) => chunks.push(event.data));
      this.recorder.addEventListener("stop", () => {
        // Turn the microphone off as soon as recording ends.
        stream.getTracks().forEach((track) => track.stop());
        this.recordedBlob = new Blob(chunks, { type: this.recorder.mimeType });
        this.showPreview(this.recordedBlob);
      });
      this.recorder.start();
      this.fileInput.value = "";
      this.startButton.disabled = true;
      this.stopButton.disabled = false;
      this.recordingNote.hidden = false;
      this.status.hidden = true;
    } catch {
      showStatus(this.status, "error", "Microphone access was denied or is not available.");
    }
  }

  stop() {
    this.recorder.stop();
    this.startButton.disabled = false;
    this.stopButton.disabled = true;
    this.recordingNote.hidden = true;
  }

  // Returns the chosen file or the last recording as WAV, or throws if there is neither.
  async wav() {
    // A newly chosen file wins over an older recording.
    const source = this.fileInput.files[0] || this.recordedBlob;
    if (!source) {
      throw new Error("Please record or choose an audio file first.");
    }
    return toWav(source);
  }

  clear() {
    this.recordedBlob = null;
    this.fileInput.value = "";
    this.preview.hidden = true;
    this.preview.removeAttribute("src");
  }
}

// --- Text to speech: send the text to Flask, which asks Azure for a WAV file ---

const ttsText = document.getElementById("tts-text");
const ttsVoice = document.getElementById("tts-voice");
const ttsButton = document.getElementById("tts-synthesize");
const ttsStatus = document.getElementById("tts-status");
const ttsResult = document.getElementById("tts-result");
const ttsAudio = document.getElementById("tts-audio");
const ttsDownload = document.getElementById("tts-download");

// Asks the API to read text aloud and returns a URL for the WAV it sends back.
async function speechUrl(text, voice) {
  const response = await fetch("/api/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return URL.createObjectURL(await response.blob());
}

ttsButton.addEventListener("click", () =>
  withStatus(ttsButton, ttsStatus, "Synthesizing…", async () => {
    const url = await speechUrl(ttsText.value, ttsVoice.value);
    ttsAudio.src = url;
    ttsDownload.href = url;
    ttsResult.hidden = false;
    return "✓ Speech synthesized successfully!";
  })
);

document.getElementById("tts-clear").addEventListener("click", () => {
  ttsText.value = "";
  ttsStatus.hidden = true;
  ttsResult.hidden = true;
  ttsAudio.removeAttribute("src");
});

// --- Speech to text ---

const sttStatus = document.getElementById("stt-status");
const sttInput = new AudioInput("stt", sttStatus);
const sttButton = document.getElementById("stt-transcribe");
const sttResult = document.getElementById("stt-result");
const sttText = document.getElementById("stt-text");

sttButton.addEventListener("click", () =>
  withStatus(sttButton, sttStatus, "Transcribing…", async () => {
    const form = new FormData();
    form.append("audio", await sttInput.wav(), "audio.wav");
    form.append("language", document.getElementById("stt-language").value);
    const data = await (await postForm("/api/stt", form)).json();
    sttText.textContent = data.text;
    sttResult.hidden = false;
    return "✓ Audio transcribed successfully!";
  })
);

document.getElementById("stt-clear").addEventListener("click", () => {
  sttInput.clear();
  sttResult.hidden = true;
  sttStatus.hidden = true;
});

document.getElementById("stt-copy").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(sttText.textContent);
    showStatus(sttStatus, "success", "✓ Text copied to clipboard.");
  } catch {
    showStatus(sttStatus, "error", "Could not copy the text.");
  }
});

// --- Diarization: lines arrive one by one while Azure is still working ---

const diaStatus = document.getElementById("dia-status");
const diaInput = new AudioInput("dia", diaStatus);
const diaButton = document.getElementById("dia-run");
const diaLines = document.getElementById("dia-lines");
const SPEAKER_COLORS = ["#6a5acd", "#e67e22", "#16a085", "#c0392b", "#2980b9", "#8e44ad"];

function speakerColor(speakers, speaker) {
  if (!speakers.has(speaker)) {
    speakers.set(speaker, SPEAKER_COLORS[speakers.size % SPEAKER_COLORS.length]);
  }
  return speakers.get(speaker);
}

function addSpeakerLine(speakers, phrase) {
  const item = document.createElement("li");
  item.style.setProperty("--speaker-color", speakerColor(speakers, phrase.speaker));
  const name = document.createElement("span");
  name.className = "speaker";
  name.textContent = phrase.speaker;
  item.append(name, phrase.text);
  diaLines.append(item);
}

diaButton.addEventListener("click", () =>
  withStatus(diaButton, diaStatus, "Listening for speakers… lines appear as they are recognized.", async () => {
    const form = new FormData();
    form.append("audio", await diaInput.wav(), "audio.wav");
    form.append("language", document.getElementById("dia-language").value);
    const response = await postForm("/api/diarize", form);

    diaLines.replaceChildren();
    diaLines.hidden = false;
    const speakers = new Map();
    let lineCount = 0;

    // The API sends one JSON object per line; read them as they arrive.
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let newline;
      while ((newline = buffer.indexOf("\n")) >= 0) {
        const line = buffer.slice(0, newline).trim();
        buffer = buffer.slice(newline + 1);
        if (!line) continue;
        const message = JSON.parse(line);
        if (message.error) throw new Error(message.error);
        if (message.speaker) {
          addSpeakerLine(speakers, message);
          lineCount += 1;
        }
      }
    }
    return `✓ ${lineCount} phrase(s) from ${speakers.size} speaker(s).`;
  })
);

document.getElementById("dia-clear").addEventListener("click", () => {
  diaInput.clear();
  diaLines.replaceChildren();
  diaLines.hidden = true;
  diaStatus.hidden = true;
});

// --- Translation ---

const trStatus = document.getElementById("tr-status");
const trInput = new AudioInput("tr", trStatus);
const trButton = document.getElementById("tr-run");
const trResult = document.getElementById("tr-result");
const trAudio = document.getElementById("tr-audio");
const trSpeak = document.getElementById("tr-speak");
let translation = null;

trButton.addEventListener("click", () =>
  withStatus(trButton, trStatus, "Translating…", async () => {
    const form = new FormData();
    form.append("audio", await trInput.wav(), "audio.wav");
    form.append("source", document.getElementById("tr-source").value);
    form.append("target", document.getElementById("tr-target").value);
    translation = await (await postForm("/api/translate", form)).json();
    document.getElementById("tr-recognized").textContent = translation.recognized;
    document.getElementById("tr-translation").textContent = translation.translation;
    trAudio.hidden = true;
    trResult.hidden = false;
    return "✓ Speech translated successfully!";
  })
);

trSpeak.addEventListener("click", () =>
  withStatus(trSpeak, trStatus, "Synthesizing the translation…", async () => {
    // The API picked a voice that speaks the target language.
    trAudio.src = await speechUrl(translation.translation, translation.voice);
    trAudio.hidden = false;
    trAudio.play();
    return "✓ Playing the translation.";
  })
);

document.getElementById("tr-clear").addEventListener("click", () => {
  trInput.clear();
  trResult.hidden = true;
  trStatus.hidden = true;
});

// --- Pronunciation assessment ---

const paStatus = document.getElementById("pa-status");
const paInput = new AudioInput("pa", paStatus);
const paButton = document.getElementById("pa-run");
const paResult = document.getElementById("pa-result");
const SCORE_ORDER = ["pronunciation", "accuracy", "fluency", "completeness", "prosody"];

function wordClass(word) {
  if (word.error === "Omission") return "omission";
  if (word.accuracy >= 80) return "good";
  if (word.accuracy >= 60) return "fair";
  return "poor";
}

function showAssessment(data) {
  const scores = document.getElementById("pa-scores");
  scores.replaceChildren(
    ...SCORE_ORDER.map((name) => {
      const tile = document.createElement("div");
      tile.className = "score";
      const value = document.createElement("strong");
      value.textContent = Math.round(data.scores[name]);
      const label = document.createElement("span");
      label.textContent = name;
      tile.append(value, label);
      return tile;
    })
  );

  const words = document.getElementById("pa-words");
  words.replaceChildren(
    ...data.words.map((word) => {
      const chip = document.createElement("span");
      chip.className = `word ${wordClass(word)}`;
      chip.textContent = word.word;
      chip.title = word.error === "None"
        ? `Accuracy ${Math.round(word.accuracy)}`
        : `${word.error}, accuracy ${Math.round(word.accuracy)}`;
      return chip;
    })
  );
  document.getElementById("pa-recognized").textContent = data.recognized;
  paResult.hidden = false;
}

paButton.addEventListener("click", () =>
  withStatus(paButton, paStatus, "Assessing pronunciation…", async () => {
    const form = new FormData();
    form.append("audio", await paInput.wav(), "audio.wav");
    form.append("reference", document.getElementById("pa-reference").value);
    showAssessment(await (await postForm("/api/pronunciation", form)).json());
    return "✓ Pronunciation assessed. Hover over a word to see its score.";
  })
);

document.getElementById("pa-clear").addEventListener("click", () => {
  paInput.clear();
  paResult.hidden = true;
  paStatus.hidden = true;
});
