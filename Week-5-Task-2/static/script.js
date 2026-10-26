// Voice calculator. Arithmetic runs on the Flask server (/api/calculate), speech runs on
// Azure through Flask (/api/speak, /api/voice). This file wires keys, voice and sound.
const display = document.getElementById("display");
const mic = document.getElementById("mic");
const voiceStatus = document.getElementById("voice-status");
const keyButtons = new Map(
  [...document.querySelectorAll("[data-key]")].map((button) => [button.dataset.key, button])
);
const OPERATIONS = { "÷": "divide", "×": "multiply", "−": "subtract", "+": "add" };

// --- Calculator state (same logic as Week 4) ---

let firstOperand = null;
let pendingOperation = null;
let startNewNumber = true;

function showValue(value) {
  display.classList.remove("error");
  display.textContent = value;
}

function showError(message) {
  display.classList.add("error");
  display.textContent = message;
  firstOperand = null;
  pendingOperation = null;
  startNewNumber = true;
}

function formatResult(value) {
  // Hide float noise such as 0.1 + 0.2 = 0.30000000000000004.
  return String(Number(value.toPrecision(12)));
}

async function requestCalculation(a, b, operation) {
  const response = await fetch("/api/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ a, b, operation }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error);
  }
  return data.result;
}

// Sends the pending operation to the server; returns false if it failed.
async function resolvePending() {
  try {
    const result = await requestCalculation(firstOperand, Number(display.textContent), pendingOperation);
    showValue(formatResult(result));
    firstOperand = result;
    return true;
  } catch (error) {
    showError(error.message);
    return false;
  }
}

function inputDigit(digit) {
  if (startNewNumber || display.classList.contains("error")) {
    showValue(digit === "." ? "0." : digit);
    startNewNumber = false;
    return;
  }
  if (digit === "." && display.textContent.includes(".")) {
    return;
  }
  showValue(display.textContent === "0" && digit !== "." ? digit : display.textContent + digit);
}

async function inputOperation(operation) {
  if (display.classList.contains("error")) {
    return;
  }
  // Chained input such as 10 + 5 × 2: resolve 10 + 5 first, like a pocket calculator.
  if (pendingOperation && !startNewNumber) {
    if (!(await resolvePending())) {
      return;
    }
  } else {
    firstOperand = Number(display.textContent);
  }
  pendingOperation = operation;
  startNewNumber = true;
}

async function inputEquals() {
  if (!pendingOperation || startNewNumber) {
    return;
  }
  await resolvePending();
  pendingOperation = null;
  startNewNumber = true;
}

function clearAll() {
  firstOperand = null;
  pendingOperation = null;
  startNewNumber = true;
  showValue("0");
}

// --- The calculator speaks ---

const audioUrls = new Map(); // text → Promise of an object URL, so each word is fetched once
let speechQueue = Promise.resolve();
let speechWarningShown = false;

function audioUrl(text) {
  if (!audioUrls.has(text)) {
    const request = fetch("/api/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }).then(async (response) => {
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || `Speech failed (${response.status}).`);
      }
      return URL.createObjectURL(await response.blob());
    });
    // Forget failures so the word can be tried again later.
    request.catch(() => audioUrls.delete(text));
    audioUrls.set(text, request);
  }
  return audioUrls.get(text);
}

function playUrl(url) {
  return new Promise((resolve) => {
    const audio = new Audio(url);
    audio.addEventListener("ended", resolve);
    audio.addEventListener("error", resolve);
    audio.play().catch(resolve);
  });
}

// Queues text to be spoken after everything queued before it, so words never overlap.
function say(text) {
  const url = audioUrl(text);
  speechQueue = speechQueue
    .then(() => url)
    .then(playUrl)
    .catch((error) => {
      // Speech is a bonus: if Azure is unavailable the calculator still works.
      if (!speechWarningShown) {
        speechWarningShown = true;
        setStatus(`Sound is off: ${error.message}`, true);
      }
    });
}

// --- Keys: clicks, keyboard and voice commands all go through pressKey ---

let keyQueue = Promise.resolve();

function flash(key) {
  const button = keyButtons.get(key);
  button.classList.add("pressed");
  setTimeout(() => button.classList.remove("pressed"), 150);
}

async function pressKey(key) {
  flash(key);
  if (key === "=") {
    await inputEquals();
    // "is eight", or the error message, e.g. "Cannot divide by zero."
    say(display.classList.contains("error") ? display.textContent : `is ${display.textContent}`);
  } else if (key in OPERATIONS) {
    say(keyButtons.get(key).dataset.word);
    await inputOperation(OPERATIONS[key]);
  } else {
    say(keyButtons.get(key).dataset.word);
    inputDigit(key);
  }
}

// Presses run one after another, so fast clicks and voice commands keep their order.
function queueKey(key) {
  keyQueue = keyQueue.then(() => pressKey(key));
  return keyQueue;
}

keyButtons.forEach((button, key) => button.addEventListener("click", () => queueKey(key)));

const KEYBOARD_KEYS = { "+": "+", "-": "−", "*": "×", "x": "×", "/": "÷", "Enter": "=", "=": "=" };
document.addEventListener("keydown", (event) => {
  if (/^[0-9.]$/.test(event.key)) queueKey(event.key);
  else if (event.key in KEYBOARD_KEYS) queueKey(KEYBOARD_KEYS[event.key]);
  else if (event.key === "Escape") clearAll();
  else return;
  // Without this, Enter would also "click" the last focused button a second time.
  event.preventDefault();
});

// --- The calculator listens: microphone → WAV → /api/voice → keys ---

function setStatus(message, isError = false) {
  voiceStatus.textContent = message;
  voiceStatus.classList.toggle("error", isError);
}

// Azure's Python SDK reads 16-bit PCM WAV; 16 kHz mono is what speech recognition expects.
const TARGET_SAMPLE_RATE = 16000;

async function toWav(blob) {
  const context = new AudioContext();
  let decoded;
  try {
    decoded = await context.decodeAudioData(await blob.arrayBuffer());
  } catch {
    throw new Error("The recording could not be read. Please try again.");
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

let recorder = null;

async function startListening() {
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    setStatus("Microphone access was denied or is not available.", true);
    return;
  }
  const chunks = [];
  // Keep a local reference: stopListening() clears `recorder` before the "stop" event fires.
  const mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.addEventListener("dataavailable", (event) => chunks.push(event.data));
  mediaRecorder.addEventListener("stop", () => {
    // Turn the microphone off as soon as recording ends.
    stream.getTracks().forEach((track) => track.stop());
    runVoiceCommand(new Blob(chunks, { type: mediaRecorder.mimeType }));
  });
  mediaRecorder.start();
  recorder = mediaRecorder;
  mic.classList.add("listening");
  setStatus("Listening… say e.g. “five plus two is”, then click 🎙️ again.");
}

function stopListening() {
  mic.classList.remove("listening");
  recorder.stop();
  recorder = null;
}

async function runVoiceCommand(recording) {
  mic.disabled = true;
  setStatus("Recognizing…");
  try {
    const form = new FormData();
    form.append("audio", await toWav(recording), "command.wav");
    const response = await fetch("/api/voice", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error);
    }
    setStatus(`Heard: “${data.heard}” → ${data.keys.join(" ")}`);
    // Press the keys one by one, exactly as if they had been clicked.
    for (const key of data.keys) {
      await queueKey(key);
    }
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    mic.disabled = false;
  }
}

mic.addEventListener("click", () => (recorder ? stopListening() : startListening()));

// --- Fetch every key's word in the background, so the first presses speak without delay ---

(async () => {
  for (const button of keyButtons.values()) {
    try {
      await audioUrl(button.dataset.word);
    } catch {
      break; // Azure is not reachable; say() will report it on the first key press.
    }
  }
})();
