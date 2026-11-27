// AI Art Chat front end: paints images, records the voice and talks to the chatbot.

const $ = (id) => document.getElementById(id);
const messages = [];  // the conversation, sent to the server with every new message

// ---------- Small helpers ----------

async function postJSON(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

function addBubble(text, kind) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${kind}`;
  bubble.textContent = text;
  if (kind === "bot") {
    bubble.title = "Click to use this text as the image prompt";
    bubble.addEventListener("click", () => { $("prompt").value = text; $("prompt").focus(); });
  }
  $("chat").appendChild(bubble);
  $("chat").scrollTop = $("chat").scrollHeight;
  return bubble;
}

// ---------- 1) Prompt -> image ----------

async function paint() {
  const prompt = $("prompt").value.trim();
  if (!prompt) { $("prompt").focus(); return; }
  $("paint").disabled = true;
  $("image-spinner").hidden = false;
  try {
    const { image } = await postJSON("/api/image", { prompt });
    $("image").src = `data:image/png;base64,${image}`;
    $("image").hidden = false;
    $("image-placeholder").hidden = true;
  } catch (error) {
    alert(error.message);
  } finally {
    $("paint").disabled = false;
    $("image-spinner").hidden = true;
  }
}

$("paint").addEventListener("click", paint);
$("prompt").addEventListener("keydown", (event) => { if (event.key === "Enter") paint(); });

// ---------- 2) Mic -> text in the message box ----------

let recorder = null;

async function toggleRecording() {
  if (recorder && recorder.state === "recording") {
    recorder.stop();  // the "stop" handler below sends the recording
    return;
  }
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    alert("Microphone access is needed to speak.");
    return;
  }
  const chunks = [];
  recorder = new MediaRecorder(stream);
  recorder.addEventListener("dataavailable", (event) => chunks.push(event.data));
  recorder.addEventListener("stop", async () => {
    stream.getTracks().forEach((track) => track.stop());  // turn the microphone off
    $("mic").classList.remove("recording");
    $("mic").disabled = true;
    $("message").placeholder = "Transcribing...";
    const form = new FormData();
    form.append("audio", new Blob(chunks, { type: recorder.mimeType }), "speech");
    try {
      const response = await fetch("/api/transcribe", { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      $("message").value = data.text;
      $("message").focus();
    } catch (error) {
      alert(error.message || "Could not transcribe the recording.");
    } finally {
      $("mic").disabled = false;
      $("message").placeholder = "Type or speak...";
    }
  });
  recorder.start();
  $("mic").classList.add("recording");
  $("message").placeholder = "Listening... press the mic again to stop";
}

$("mic").addEventListener("click", toggleRecording);

// ---------- 3) Message -> chatbot -> both in the chat history ----------

async function send() {
  const text = $("message").value.trim();
  if (!text) { $("message").focus(); return; }
  $("message").value = "";
  addBubble(text, "user");
  messages.push({ role: "user", content: text });

  $("send").disabled = true;
  const typing = addBubble("Thinking...", "bot typing");
  try {
    const { reply } = await postJSON("/api/chat", { messages });
    typing.remove();
    addBubble(reply, "bot");
    messages.push({ role: "assistant", content: reply });
  } catch (error) {
    typing.remove();
    addBubble(error.message, "bot error");
    messages.pop();  // do not keep a message the bot never answered
  } finally {
    $("send").disabled = false;
  }
}

$("send").addEventListener("click", send);
$("message").addEventListener("keydown", (event) => { if (event.key === "Enter") send(); });
