// Shows the chosen image, sends it to Flask, and draws the answer. The model runs in the Cog container.
const form = document.getElementById("form");
const imageInput = document.getElementById("image");
const fileName = document.getElementById("file-name");
const preview = document.getElementById("preview");
const classifyButton = document.getElementById("classify");
const errorBox = document.getElementById("error");
const result = document.getElementById("result");
const resultLabel = document.getElementById("result-label");
const resultClass = document.getElementById("result-class");
const resultConfidence = document.getElementById("result-confidence");
const kindsList = document.getElementById("kinds");

function percent(probability) {
  return `${(probability * 100).toFixed(1)}%`;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function kindRow({ kind, probability }) {
  const item = document.createElement("li");

  const row = document.createElement("div");
  row.className = "kind-row";
  const name = document.createElement("span");
  name.textContent = kind;
  const value = document.createElement("span");
  value.textContent = percent(probability);
  row.append(name, value);

  const bar = document.createElement("div");
  bar.className = "kind-bar";
  const fill = document.createElement("div");
  fill.className = "kind-fill";
  fill.style.width = percent(probability);
  bar.append(fill);

  item.append(row, bar);
  return item;
}

function showResult(prediction) {
  resultLabel.textContent = prediction.is_cat
    ? "This looks like a"
    : "This does not look like a cat. The model sees a";
  resultClass.textContent = prediction.predicted_class;
  resultConfidence.textContent = `${percent(prediction.confidence)} confidence`;
  // The cat kinds would all be near 0% for an image without a cat, so they are only shown for cats.
  kindsList.replaceChildren(...(prediction.is_cat ? prediction.top_kinds.map(kindRow) : []));
  result.hidden = false;
}

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  errorBox.hidden = true;
  result.hidden = true;
  classifyButton.disabled = !file;
  fileName.textContent = file ? file.name : "No image chosen";
  preview.hidden = !file;
  if (preview.src) URL.revokeObjectURL(preview.src);
  if (file) preview.src = URL.createObjectURL(file);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  result.hidden = true;
  classifyButton.disabled = true;
  classifyButton.textContent = "Classifying…";
  try {
    const body = new FormData();
    body.append("image", imageInput.files[0]);
    const response = await fetch("/api/classify", { method: "POST", body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    showResult(data);
  } catch (error) {
    showError(error.message);
  } finally {
    classifyButton.disabled = false;
    classifyButton.textContent = "Classify";
  }
});
