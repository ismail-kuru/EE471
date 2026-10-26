// Text-to-speech: send the text to Flask, which asks Azure for a WAV file.
const ttsText = document.getElementById("tts-text");
const ttsVoice = document.getElementById("tts-voice");
const ttsButton = document.getElementById("tts-synthesize");
const ttsStatus = document.getElementById("tts-status");
const ttsResult = document.getElementById("tts-result");
const ttsAudio = document.getElementById("tts-audio");
const ttsDownload = document.getElementById("tts-download");

let audioUrl = null;

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
    // Free the previous recording's memory before making a new URL.
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
