const DISPLAY_WIDTH = 64;
const DISPLAY_HEIGHT = 32;
const SCALE = 10;

const statusEl = document.querySelector("#status");
const canvas = document.querySelector("#screen");
const ctx = canvas.getContext("2d");
const runPauseButton = document.querySelector("#runPause");
const stepButton = document.querySelector("#step");
const stepFrameButton = document.querySelector("#stepFrame");
const runToDrawButton = document.querySelector("#runToDraw");
const resetButton = document.querySelector("#reset");
const romFileInput = document.querySelector("#romFile");
const speedInput = document.querySelector("#speed");
const speedValue = document.querySelector("#speedValue");
const debugRateInput = document.querySelector("#debugRate");
const registersEl = document.querySelector("#registers");
const keysEl = document.querySelector("#keys");
const memoryEl = document.querySelector("#memory");
const traceEl = document.querySelector("#trace");

const fields = {
  opcode: document.querySelector("#opcode"),
  decoded: document.querySelector("#decoded"),
  pc: document.querySelector("#pc"),
  index: document.querySelector("#index"),
  delay: document.querySelector("#delay"),
  sound: document.querySelector("#sound"),
  stack: document.querySelector("#stack"),
};

const chip8KeyLabels = ["X", "1", "2", "3", "Q", "W", "E", "A", "S", "D", "Z", "C", "4", "R", "F", "V"];
const keyMap = new Map(chip8KeyLabels.map((key, index) => [key.toLowerCase(), index]));

let pyodide = null;
let createEmulator = null;
let emulator = null;
let romBytes = null;
let running = false;
let cyclesPerFrame = Number(speedInput.value);
let keys = Array(16).fill(false);
let audioContext = null;
let oscillator = null;
let previousRegisters = null;
let lastDebugRender = 0;
let debugInterval = Number(debugRateInput.value);

function setStatus(message, state = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${state}`.trim();
}

function formatStack(stack) {
  if (!stack.length) return "[]";
  return `[${stack.join(", ")}]`;
}

function buildRegisters() {
  registersEl.replaceChildren();
  for (let i = 0; i < 16; i += 1) {
    const cell = document.createElement("div");
    cell.className = "register";
    cell.innerHTML = `<span>V${i.toString(16).toUpperCase()}</span><strong id="reg-${i}">00</strong>`;
    registersEl.appendChild(cell);
  }
}

function buildKeypad() {
  keysEl.replaceChildren();
  chip8KeyLabels.forEach((label, index) => {
    const key = document.createElement("div");
    key.id = `key-${index}`;
    key.className = "key";
    key.innerHTML = `<span>${index.toString(16).toUpperCase()}</span><strong>${label}</strong>`;
    keysEl.appendChild(key);
  });
}

function drawDisplay(display = []) {
  ctx.fillStyle = "#11151c";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#79ffe1";

  for (let y = 0; y < DISPLAY_HEIGHT; y += 1) {
    for (let x = 0; x < DISPLAY_WIDTH; x += 1) {
      if (display[y * DISPLAY_WIDTH + x]) {
        ctx.fillRect(x * SCALE, y * SCALE, SCALE - 1, SCALE - 1);
      }
    }
  }
}

function getSnapshot() {
  if (!emulator) return null;
  const snapshotProxy = emulator.snapshot();
  const snapshot = snapshotProxy.toJs({ dict_converter: Object.fromEntries });
  snapshotProxy.destroy();
  return snapshot;
}

function renderDebug(snapshot) {
  if (!snapshot) return;

  fields.opcode.textContent = snapshot.lastOpcode;
  fields.decoded.textContent = snapshot.lastDecoded;
  fields.pc.textContent = snapshot.pc;
  fields.index.textContent = snapshot.index;
  fields.delay.textContent = snapshot.delayTimer;
  fields.sound.textContent = snapshot.soundTimer;
  fields.stack.textContent = formatStack(snapshot.stack);

  snapshot.registers.forEach((value, index) => {
    const valueEl = document.querySelector(`#reg-${index}`);
    const cell = valueEl.closest(".register");
    const changed = previousRegisters && previousRegisters[index] !== value;
    valueEl.textContent = value;
    cell.classList.toggle("changed", changed);
  });
  previousRegisters = [...snapshot.registers];

  memoryEl.replaceChildren();
  snapshot.memoryWindow.forEach((row) => {
    const line = document.createElement("div");
    line.className = row.current ? "memory-line current" : "memory-line";
    line.innerHTML = `<span>${row.address}</span><strong>${row.opcode}</strong><em>${row.decoded}</em>`;
    memoryEl.appendChild(line);
  });

  keys.forEach((pressed, index) => {
    document.querySelector(`#key-${index}`).classList.toggle("pressed", pressed);
  });

  traceEl.replaceChildren();
  [...snapshot.trace].reverse().forEach((row, index) => {
    const line = document.createElement("div");
    line.className = index === 0 ? "trace-line latest" : "trace-line";
    line.innerHTML = `<span>${row.pc}</span><strong>${row.opcode}</strong><em>${row.decoded}</em>`;
    traceEl.appendChild(line);
  });
}

function updateSound(soundTimer) {
  if (soundTimer > 0 && !oscillator) {
    audioContext ??= new AudioContext();
    oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.frequency.value = 440;
    gain.gain.value = 0.025;
    oscillator.connect(gain).connect(audioContext.destination);
    oscillator.start();
  }

  if (soundTimer <= 0 && oscillator) {
    oscillator.stop();
    oscillator.disconnect();
    oscillator = null;
  }
}

function runFrame() {
  const now = performance.now();

  if (emulator && running) {
    emulator.set_inputs(keys);
    emulator.run_cycles(cyclesPerFrame);
    emulator.tick_timers();
  }

  const snapshot = getSnapshot();
  if (snapshot) {
    drawDisplay(snapshot.display);
    if (!running || debugInterval === 0 || now - lastDebugRender >= debugInterval) {
      renderDebug(snapshot);
      lastDebugRender = now;
    }
    updateSound(snapshot.soundTimer);
  }

  requestAnimationFrame(runFrame);
}

function setControlsEnabled(enabled) {
  runPauseButton.disabled = !enabled;
  stepButton.disabled = !enabled;
  stepFrameButton.disabled = !enabled;
  runToDrawButton.disabled = !enabled;
  resetButton.disabled = !enabled;
}

function makeEmulator(bytes) {
  if (emulator) {
    emulator.destroy();
  }

  romBytes = Array.from(bytes);
  emulator = createEmulator(romBytes);
  running = false;
  previousRegisters = null;
  lastDebugRender = 0;
  runPauseButton.textContent = "Run";
  setControlsEnabled(true);
  const snapshot = getSnapshot();
  drawDisplay(snapshot.display);
  renderDebug(snapshot);
  setStatus(`Loaded ${romBytes.length} byte ROM`, "ready");
}

async function loadBuiltInRom() {
  const response = await fetch("./roms/br8kout.ch8");
  if (!response.ok) throw new Error("Could not load built-in ROM");
  const buffer = await response.arrayBuffer();
  makeEmulator(new Uint8Array(buffer));
}

async function boot() {
  buildRegisters();
  buildKeypad();
  drawDisplay();

  try {
    pyodide = await loadPyodide();
    const chip8Source = await fetch("../chip8.py").then((response) => {
      if (!response.ok) throw new Error("Could not load shared chip8.py");
      return response.text();
    });
    const adapterSource = await fetch("./chip8_browser.py").then((response) => {
      if (!response.ok) throw new Error("Could not load Pyodide adapter");
      return response.text();
    });
    pyodide.FS.writeFile("chip8.py", chip8Source);
    await pyodide.runPythonAsync(adapterSource);
    createEmulator = pyodide.globals.get("create_emulator");
    await loadBuiltInRom();
    requestAnimationFrame(runFrame);
  } catch (error) {
    console.error(error);
    setStatus("Pyodide failed to load. Use a local server and check internet access.", "error");
  }
}

runPauseButton.addEventListener("click", async () => {
  if (!emulator) return;
  if (!audioContext) {
    audioContext = new AudioContext();
  }
  if (audioContext.state === "suspended") {
    await audioContext.resume();
  }
  running = !running;
  runPauseButton.textContent = running ? "Pause" : "Run";
});

stepButton.addEventListener("click", () => {
  if (!emulator) return;
  running = false;
  runPauseButton.textContent = "Run";
  emulator.set_inputs(keys);
  emulator.cycle();
  const snapshot = getSnapshot();
  drawDisplay(snapshot.display);
  renderDebug(snapshot);
});

stepFrameButton.addEventListener("click", () => {
  if (!emulator) return;
  running = false;
  runPauseButton.textContent = "Run";
  emulator.set_inputs(keys);
  emulator.run_cycles(cyclesPerFrame);
  emulator.tick_timers();
  const snapshot = getSnapshot();
  drawDisplay(snapshot.display);
  renderDebug(snapshot);
});

runToDrawButton.addEventListener("click", () => {
  if (!emulator) return;
  running = false;
  runPauseButton.textContent = "Run";
  emulator.set_inputs(keys);
  const cyclesProxy = emulator.run_until_draw(2000);
  const cycles = Number(cyclesProxy);
  emulator.tick_timers();
  const snapshot = getSnapshot();
  drawDisplay(snapshot.display);
  renderDebug(snapshot);
  setStatus(`Stopped after ${cycles} cycle${cycles === 1 ? "" : "s"}`, "ready");
});

resetButton.addEventListener("click", () => {
  if (!emulator) return;
  running = false;
  previousRegisters = null;
  lastDebugRender = 0;
  runPauseButton.textContent = "Run";
  emulator.reset();
  const snapshot = getSnapshot();
  drawDisplay(snapshot.display);
  renderDebug(snapshot);
  setStatus(`Reset ${romBytes.length} byte ROM`, "ready");
});

romFileInput.addEventListener("change", async (event) => {
  const [file] = event.target.files;
  if (!file) return;
  const buffer = await file.arrayBuffer();
  makeEmulator(new Uint8Array(buffer));
  setStatus(`Loaded ${file.name}`, "ready");
});

speedInput.addEventListener("input", () => {
  cyclesPerFrame = Number(speedInput.value);
  speedValue.textContent = String(cyclesPerFrame);
});

debugRateInput.addEventListener("change", () => {
  debugInterval = Number(debugRateInput.value);
  lastDebugRender = 0;
});

window.addEventListener("keydown", (event) => {
  const index = keyMap.get(event.key.toLowerCase());
  if (index === undefined) return;
  event.preventDefault();
  keys[index] = true;
});

window.addEventListener("keyup", (event) => {
  const index = keyMap.get(event.key.toLowerCase());
  if (index === undefined) return;
  event.preventDefault();
  keys[index] = false;
});

boot();
