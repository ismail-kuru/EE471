// Shows the chosen image, sends it to Flask, and draws both models' answers side by side.
const form = document.getElementById("form");
const imageInput = document.getElementById("image");
const fileName = document.getElementById("file-name");
const preview = document.getElementById("preview");
const classifyButton = document.getElementById("classify");
const errorBox = document.getElementById("error");
const result = document.getElementById("result");
const agreement = document.getElementById("agreement");
const title = document.getElementById("title");
const intro = document.getElementById("intro");
const segments = document.querySelectorAll(".segment");

const DATASET_TEXT = {
  fashion: {
    title: "Garment Classifier",
    intro: "Upload a picture of a piece of clothing and compare what the two models see.",
  },
  cifar10: {
    title: "CIFAR10 Classifier",
    intro: "Upload a picture of a plane, car, bird, cat, deer, dog, frog, horse, ship or truck, and compare what the two models see.",
  },
};
let dataset = "fashion";

function percent(probability) {
  return `${(probability * 100).toFixed(1)}%`;
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function classRow(entry) {
  const row = element("div", "kind-row");
  row.append(element("span", "", entry.class), element("span", "", percent(entry.probability)));

  const fill = element("div", "kind-fill");
  fill.style.width = percent(entry.probability);
  const bar = element("div", "kind-bar");
  bar.append(fill);

  const item = element("li");
  item.append(row, bar);
  return item;
}

function settingsText({ lr, momentum, batch_size, epochs }) {
  const momentumText = momentum ? `, momentum ${momentum}` : "";
  return `Learning rate ${lr}${momentumText}, batch size ${batch_size}, ${epochs} epochs`;
}

function showModel(id, prediction) {
  const area = document.querySelector(`#${id} .model-result`);
  if (prediction.error) {
    area.replaceChildren(element("p", "error", prediction.error));
    return;
  }
  const classes = element("ul", "kinds");
  classes.append(...prediction.top_classes.map(classRow));
  area.replaceChildren(
    element("p", "result-class", prediction.predicted_class),
    element("p", "result-confidence", `${percent(prediction.confidence)} confidence`),
    classes,
    element("p", "model-info", `Test accuracy: ${percent(prediction.test_accuracy)}`),
    element("p", "model-info", settingsText(prediction.hyperparameters))
  );
}

function agreementText({ baseline, optimized }) {
  if (baseline.error || optimized.error) return "Only one model could answer.";
  return baseline.predicted_class === optimized.predicted_class
    ? "Both models agree."
    : "The models disagree.";
}

function showResult(data) {
  showModel("baseline", data.baseline);
  showModel("optimized", data.optimized);
  agreement.textContent = agreementText(data);
  result.hidden = false;
}

segments.forEach((segment) => {
  segment.addEventListener("click", () => {
    dataset = segment.dataset.dataset;
    segments.forEach((other) => other.classList.toggle("active", other === segment));
    title.textContent = DATASET_TEXT[dataset].title;
    intro.textContent = DATASET_TEXT[dataset].intro;
    // The old answer came from the other dataset's models.
    errorBox.hidden = true;
    result.hidden = true;
  });
});

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
    body.append("dataset", dataset);
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
