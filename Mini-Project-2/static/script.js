// The page holds no library rules: filtering, validation and state checks all
// happen in the API. This file only sends requests and draws what comes back.

const list = document.getElementById("item-list");
const emptyState = document.getElementById("empty-state");
const errorArea = document.getElementById("error-area");
const errorMessage = document.getElementById("error-message");
const availableOnly = document.getElementById("available-only");
const segments = document.querySelectorAll(".segment");

const dialog = document.getElementById("item-dialog");
const form = document.getElementById("item-form");
const dialogTitle = document.getElementById("dialog-title");
const titleField = document.getElementById("field-title");
const authorField = document.getElementById("field-author");
const typeField = document.getElementById("field-type");
const sizeField = document.getElementById("field-size");
const sizeLabel = document.getElementById("size-label");
const formError = document.getElementById("form-error");

const SIZE_FIELD = { book: "page_count", dvd: "duration" };
const SIZE_LABEL = { book: "Page Count", dvd: "Duration (minutes)" };

const ICONS = {
  edit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>',
  delete: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/></svg>',
  book: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h7a3 3 0 0 1 3 3v13a2 2 0 0 0-2-2H2Z"/><path d="M22 4h-7a3 3 0 0 0-3 3v13a2 2 0 0 1 2-2h8Z"/></svg>',
  dvd: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
};

// available is "true", "false" or "" (no filter); the same strings the API takes.
let filters = { available: "", type: "" };
let editingId = null;

// --- API ---

async function api(method, url, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(url, options);
  // 204 No Content (successful delete) has no body to parse.
  let data = null;
  if (response.status !== 204) {
    try {
      data = await response.json();
    } catch {
      // e.g. an unexpected HTML error page instead of JSON.
      throw new Error(`Unexpected response from the server (${response.status}).`);
    }
  }
  if (!response.ok) {
    throw new Error(data && data.error ? data.error : `Request failed (${response.status}).`);
  }
  return data;
}

function itemsUrl() {
  const params = new URLSearchParams();
  if (filters.available) params.set("available", filters.available);
  if (filters.type) params.set("type", filters.type);
  const query = params.toString();
  return query ? `/api/items?${query}` : "/api/items";
}

// --- Message area: API errors in red, success messages (e.g. the DVD reminder) in green ---

function showError(message) {
  errorMessage.textContent = message;
  errorArea.classList.remove("notice");
  errorArea.hidden = false;
}

function showNotice(message) {
  errorMessage.textContent = message;
  errorArea.classList.add("notice");
  errorArea.hidden = false;
}

function clearError() {
  errorArea.hidden = true;
  errorMessage.textContent = "";
}

// --- Rendering ---

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function iconButton(icon, label, className, onClick) {
  const button = element("button", `icon-button ${className}`);
  button.type = "button";
  button.innerHTML = ICONS[icon];
  button.setAttribute("aria-label", label);
  button.title = label;
  button.addEventListener("click", onClick);
  return button;
}

function renderCard(item) {
  const card = element("article", item.is_available ? "card" : "card checked-out");

  card.append(element("h3", "", item.title));
  card.append(element("p", "author", item.author));
  card.append(element("span", "type-badge", item.type === "dvd" ? "DVD" : "Book"));

  const meta = element("div", "meta");
  const size = element("span", "size");
  size.innerHTML = ICONS[item.type === "dvd" ? "dvd" : "book"];
  size.append(item.type === "dvd" ? `${item.duration} mins` : `${item.page_count} pages`);
  const status = item.is_available
    ? element("span", "status-badge available", "Available")
    : element("span", "status-badge out", "Checked out");
  meta.append(size, status);
  card.append(meta);

  const actions = element("div", "actions");
  const mainAction = item.is_available
    ? element("button", "button primary", "Checkout")
    : element("button", "button secondary", "Return");
  mainAction.type = "button";
  mainAction.addEventListener("click", () =>
    runAction(() => api("POST", `/api/items/${item.id}/${item.is_available ? "checkout" : "return"}`))
  );
  actions.append(
    mainAction,
    iconButton("edit", `Edit ${item.title}`, "", () => openDialog(item)),
    // Not disabled for checked-out items on purpose: the API decides and returns 409.
    iconButton("delete", `Delete ${item.title}`, "danger", () => deleteItem(item))
  );
  card.append(actions);
  return card;
}

function renderList(items) {
  list.replaceChildren(...items.map(renderCard));
  const filtered = filters.available || filters.type;
  emptyState.hidden = items.length > 0;
  emptyState.textContent = filtered
    ? "No items match these filters."
    : "No items yet. Click “+ Add Item” to add your first book or DVD.";
}

async function loadItems() {
  try {
    renderList(await api("GET", itemsUrl()));
  } catch (error) {
    showError(error.message);
  }
}

// Runs a change (checkout, return, delete) and reloads the list from the API.
async function runAction(request) {
  clearError();
  try {
    const data = await request();
    if (data && data.message) showNotice(data.message);
  } catch (error) {
    showError(error.message);
  }
  await loadItems();
}

function deleteItem(item) {
  if (!confirm(`Delete “${item.title}”?`)) return;
  runAction(() => api("DELETE", `/api/items/${item.id}`));
}

// --- Add / Edit dialog ---

function updateSizeLabel() {
  sizeLabel.textContent = SIZE_LABEL[typeField.value];
}

function openDialog(item = null) {
  editingId = item ? item.id : null;
  dialogTitle.textContent = item ? "Edit Item" : "Add New Item";
  titleField.value = item ? item.title : "";
  authorField.value = item ? item.author : "";
  typeField.value = item ? item.type : "book";
  // The API does not allow changing an item's type, so lock it while editing.
  typeField.disabled = Boolean(item);
  sizeField.value = item ? item[SIZE_FIELD[item.type]] : "";
  updateSizeLabel();
  formError.hidden = true;
  dialog.showModal();
  titleField.focus();
}

function formValues() {
  const sizeText = sizeField.value.trim();
  return {
    title: titleField.value,
    author: authorField.value,
    // Send the raw value; the API checks it is a positive integer.
    [SIZE_FIELD[typeField.value]]: sizeText === "" ? null : Number(sizeText),
  };
}

async function saveItem(event) {
  event.preventDefault();
  formError.hidden = true;
  try {
    if (editingId === null) {
      await api("POST", "/api/items", { type: typeField.value, ...formValues() });
    } else {
      await api("PUT", `/api/items/${editingId}`, formValues());
    }
  } catch (error) {
    // Keep the dialog open so the user can fix the input.
    formError.textContent = error.message;
    formError.hidden = false;
    return;
  }
  dialog.close();
  clearError();
  await loadItems();
}

// --- Event wiring ---

availableOnly.addEventListener("change", () => {
  filters.available = availableOnly.checked ? "true" : "";
  loadItems();
});

segments.forEach((segment) => {
  segment.addEventListener("click", () => {
    segments.forEach((other) => other.classList.toggle("active", other === segment));
    filters.type = segment.dataset.type;
    loadItems();
  });
});

document.getElementById("add-button").addEventListener("click", () => openDialog());
document.getElementById("cancel-button").addEventListener("click", () => dialog.close());
document.getElementById("error-close").addEventListener("click", clearError);
typeField.addEventListener("change", updateSizeLabel);
form.addEventListener("submit", saveItem);

// --- The librarian speaks ---

const mic = document.getElementById("mic");
const voiceStatus = document.getElementById("voice-status");
let currentAudio = null;

function setStatus(message, isError = false) {
  voiceStatus.textContent = message;
  voiceStatus.classList.toggle("error", isError);
}

function stopSpeaking() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
}

async function say(text) {
  stopSpeaking();
  const response = await fetch("/api/speak", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || `Speech failed (${response.status}).`);
  }
  const url = URL.createObjectURL(await response.blob());
  currentAudio = new Audio(url);
  currentAudio.addEventListener("ended", () => URL.revokeObjectURL(url));
  await currentAudio.play();
}

// Shows the sentence and reads it aloud; if sound fails, the sentence is still on screen.
async function announce(reply, ok) {
  (ok ? showNotice : showError)(reply);
  try {
    await say(reply);
  } catch (error) {
    setStatus(`Sound is off: ${error.message}`, true);
  }
}

// --- The librarian listens: microphone → WAV → /api/voice ---

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
  stopSpeaking(); // So the microphone does not record the librarian.
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
  mic.textContent = "⏹ Send";
  setStatus("Listening… say a command, then click “Send”.");
}

function stopListening() {
  mic.classList.remove("listening");
  mic.textContent = "🎙️ Speak";
  recorder.stop();
  recorder = null;
}

// Makes the filter controls match a spoken list command such as "show available DVDs".
function applyVoiceFilters(query) {
  filters = { available: query.available || "", type: query.type || "" };
  availableOnly.checked = filters.available === "true";
  segments.forEach((segment) => segment.classList.toggle("active", segment.dataset.type === filters.type));
}

async function runVoiceCommand(recording) {
  mic.disabled = true;
  setStatus("Recognizing…");
  try {
    const body = new FormData();
    body.append("audio", await toWav(recording), "command.wav");
    const response = await fetch("/api/voice", { method: "POST", body });
    const data = await response.json();
    if (!response.ok) {
      setStatus(data.error, true);
      await announce(data.error, false);
      return;
    }
    setStatus(`Heard: “${data.heard}” → ${data.request} (${data.status})`);
    if (data.action === "list") applyVoiceFilters(data.query);
    await loadItems();
    await announce(data.reply, data.ok);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    mic.disabled = false;
  }
}

mic.addEventListener("click", () => (recorder ? stopListening() : startListening()));

loadItems();
