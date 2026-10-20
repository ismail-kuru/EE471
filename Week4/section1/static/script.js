// All arithmetic happens on the Flask server; this file only tracks key presses.
const display = document.getElementById("display");

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

document.querySelectorAll("[data-digit]").forEach((key) => {
  key.addEventListener("click", () => inputDigit(key.dataset.digit));
});
document.querySelectorAll("[data-operation]").forEach((key) => {
  key.addEventListener("click", () => inputOperation(key.dataset.operation));
});
document.getElementById("equals").addEventListener("click", inputEquals);

const keyboardOperations = { "+": "add", "-": "subtract", "*": "multiply", "/": "divide" };
document.addEventListener("keydown", (event) => {
  if (/^[0-9.]$/.test(event.key)) inputDigit(event.key);
  else if (event.key in keyboardOperations) inputOperation(keyboardOperations[event.key]);
  else if (event.key === "Enter" || event.key === "=") inputEquals();
  else if (event.key === "Escape") clearAll();
  else return;
  // Without this, Enter would also "click" the last focused button a second time.
  event.preventDefault();
});
