const nodes = {
  A: { x: 70, y: 190 },
  B: { x: 220, y: 80 },
  C: { x: 220, y: 190 },
  D: { x: 220, y: 300 },
  E: { x: 430, y: 110 },
  F: { x: 430, y: 260 },
  G: { x: 650, y: 120 },
  H: { x: 650, y: 260 },
  T: { x: 860, y: 190 },
};

const edges = [
  ["A", "B"],
  ["A", "C"],
  ["A", "D"],
  ["B", "E"],
  ["B", "F"],
  ["C", "E"],
  ["C", "F"],
  ["D", "F"],
  ["E", "G"],
  ["E", "H"],
  ["F", "H"],
  ["G", "T"],
  ["H", "T"],
];

const labelOffsets = {
  "B->F": { dx: -10, dy: -10 },
  "C->E": { dx: 10, dy: 6 },
  "D->F": { dx: -12, dy: 10 },
  "E->H": { dx: 10, dy: -8 },
  "F->H": { dx: 0, dy: 12 },
};

const state = {
  currentRoundId: null,
  currentCaps: {},
  playerName: "",
  autoStartEnter: true,
  autoStartAfterSubmit: false,
  roundSubmitted: false,
  leaderboardVisible: false,
  recentResultsVisible: false,
  recentResults: [],
};

const RECENT_RESULTS_KEY = "traffic_recent_results";

const menuScreen = document.getElementById("menuScreen");
const gameScreen = document.getElementById("gameScreen");
const menuPlayerNameInput = document.getElementById("menuPlayerName");
const menuValidation = document.getElementById("menuValidation");
const activePlayerLabel = document.getElementById("activePlayerLabel");
const roundLabel = document.getElementById("roundLabel");

const startGameBtn = document.getElementById("startGameBtn");
const toggleLeaderboardBtn = document.getElementById("toggleLeaderboardBtn");
const toggleRecentResultsBtn = document.getElementById("toggleRecentResultsBtn");
const menuBtn = document.getElementById("menuBtn");
const backToHubFromMenuBtn = document.getElementById("backToHubFromMenuBtn");
const resetBoardBtn = document.getElementById("resetBoardBtn");
const menuLeaderboardSection = document.getElementById("menuLeaderboardSection");
const menuRecentResultsSection = document.getElementById("menuRecentResultsSection");

const openInstructionsBtn = document.getElementById("openInstructionsBtn");
const closeInstructionsBtn = document.getElementById("closeInstructionsBtn");
const instructionsModal = document.getElementById("instructionsModal");

const openSettingsBtn = document.getElementById("openSettingsBtn");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");
const settingsModal = document.getElementById("settingsModal");
const autoStartEnterInput = document.getElementById("autoStartEnter");
const autoStartAfterSubmitInput = document.getElementById("autoStartAfterSubmit");

const svg = document.getElementById("network");
const newRoundBtn = document.getElementById("newRoundBtn");
const submitBtn = document.getElementById("submitBtn");
const answerInput = document.getElementById("answer");
const resultBox = document.getElementById("resultBox");
const menuLeaderboardList = document.getElementById("menuLeaderboardList");
const recentResultsList = document.getElementById("recentResultsList");

function showMenu() {
  menuScreen.classList.remove("hidden");
  gameScreen.classList.add("hidden");
}

function showGame() {
  menuScreen.classList.add("hidden");
  gameScreen.classList.remove("hidden");
}

function openModal(modal) {
  modal.classList.remove("hidden");
}

function closeModal(modal) {
  modal.classList.add("hidden");
}

function setRoundSubmissionLocked(locked) {
  state.roundSubmitted = locked;
  submitBtn.disabled = locked;
  answerInput.disabled = locked;
}

function loadRecentResults() {
  try {
    const raw = window.localStorage.getItem(RECENT_RESULTS_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    if (Array.isArray(parsed)) {
      state.recentResults = parsed;
    }
  } catch {
    state.recentResults = [];
  }
}

function saveRecentResults() {
  try {
    window.localStorage.setItem(RECENT_RESULTS_KEY, JSON.stringify(state.recentResults));
  } catch {
    // Ignore storage errors in private mode.
  }
}

function renderRecentResults() {
  recentResultsList.innerHTML = "";
  if (!state.recentResults.length) {
    recentResultsList.innerHTML = '<li class="leaderboard-empty">No results yet.</li>';
    return;
  }

  state.recentResults.forEach((entry) => {
    const li = document.createElement("li");
    li.className = "leaderboard-item";
    li.innerHTML = `
      <span><span class="result-chip ${entry.result}">${entry.result.toUpperCase()}</span> ${entry.playerName}</span>
      <strong>Answer ${entry.answer} / Correct ${entry.correctMaxFlow}</strong>
    `;
    recentResultsList.appendChild(li);
  });
}

function recordRecentResult(data, answer) {
  const normalizedResult = String(data.result || "unknown").toLowerCase();

  if (normalizedResult === "win") {
    return;
  }

  state.recentResults.unshift({
    result: normalizedResult,
    playerName: state.playerName,
    answer,
    correctMaxFlow: data.correctMaxFlow,
  });

  if (state.recentResults.length > 10) {
    state.recentResults = state.recentResults.slice(0, 10);
  }

  saveRecentResults();
  renderRecentResults();
}

function setLeaderboardVisible(visible) {
  state.leaderboardVisible = visible;
  menuLeaderboardSection.classList.toggle("hidden", !visible);
  toggleLeaderboardBtn.textContent = visible ? "Hide Leaderboard" : "Show Leaderboard";

  if (visible) {
    state.recentResultsVisible = false;
    menuRecentResultsSection.classList.add("hidden");
    toggleRecentResultsBtn.textContent = "Show Recent Results";
  }
}

function toggleLeaderboard() {
  setLeaderboardVisible(!state.leaderboardVisible);
}

function setRecentResultsVisible(visible) {
  state.recentResultsVisible = visible;
  menuRecentResultsSection.classList.toggle("hidden", !visible);
  toggleRecentResultsBtn.textContent = visible ? "Hide Recent Results" : "Show Recent Results";

  if (visible) {
    state.leaderboardVisible = false;
    menuLeaderboardSection.classList.add("hidden");
    toggleLeaderboardBtn.textContent = "Show Leaderboard";
  }
}

function toggleRecentResults() {
  setRecentResultsVisible(!state.recentResultsVisible);
}

function backToHub() {
  window.location.assign("http://localhost:5175/");
}

function clearRoundView() {
  state.currentRoundId = null;
  state.currentCaps = {};
  setRoundSubmissionLocked(false);
  roundLabel.textContent = "-";
  answerInput.value = "";
  drawGraph({});
  setResult("Press New Round to start.", "warn");
}

function setResult(message, level = "warn", metrics = []) {
  const chips = metrics.length
    ? `<div class="metrics">${metrics.map((item) => `<span class="metric-chip">${item}</span>`).join("")}</div>`
    : "";

  resultBox.innerHTML = `
    <div class="section-head">
      <h2>Round Result</h2>
    </div>
    <p class="status-line ${level}">${message}</p>
    ${chips}
  `;
}

function drawGraph(capacities) {
  svg.innerHTML = `
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#7b8ba0"></path>
      </marker>
    </defs>
  `;

  for (const [from, to] of edges) {
    const a = nodes[from];
    const b = nodes[to];
    const edgeKey = `${from}->${to}`;

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", a.x);
    line.setAttribute("y1", a.y);
    line.setAttribute("x2", b.x);
    line.setAttribute("y2", b.y);
    line.setAttribute("class", "edge");
    svg.appendChild(line);

    const midX = (a.x + b.x) / 2;
    const midY = (a.y + b.y) / 2;
    const vx = b.x - a.x;
    const vy = b.y - a.y;
    const length = Math.hypot(vx, vy) || 1;
    const nx = -vy / length;
    const ny = vx / length;
    const custom = labelOffsets[edgeKey] || { dx: 0, dy: 0 };
    const labelX = midX + nx * 12 + custom.dx;
    const labelY = midY + ny * 12 + custom.dy;

    const labelGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const capText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    capText.setAttribute("x", labelX);
    capText.setAttribute("y", labelY);
    capText.setAttribute("text-anchor", "middle");
    capText.setAttribute("dominant-baseline", "middle");
    capText.setAttribute("class", "cap-label");
    capText.textContent = capacities[edgeKey] ?? "?";
    labelGroup.appendChild(capText);
    svg.appendChild(labelGroup);

    const bbox = capText.getBBox();
    const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bg.setAttribute("x", String(bbox.x - 4));
    bg.setAttribute("y", String(bbox.y - 1));
    bg.setAttribute("width", String(bbox.width + 8));
    bg.setAttribute("height", String(bbox.height + 2));
    bg.setAttribute("rx", "4");
    bg.setAttribute("class", "cap-label-bg");
    labelGroup.insertBefore(bg, capText);
  }

  for (const [label, pos] of Object.entries(nodes)) {
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", pos.x);
    circle.setAttribute("cy", pos.y);
    circle.setAttribute("r", 20);
    circle.setAttribute("class", "node");
    svg.appendChild(circle);

    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", pos.x);
    text.setAttribute("y", pos.y + 5);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("class", "node-text");
    text.textContent = label;
    svg.appendChild(text);
  }
}

async function loadLeaderboard() {
  menuLeaderboardList.innerHTML = "";
  try {
    const res = await fetch("/api/leaderboard");
    const rows = await res.json();

    if (!Array.isArray(rows) || rows.length === 0) {
      menuLeaderboardList.innerHTML = '<li class="leaderboard-empty">No winners yet.</li>';
      return;
    }

    rows.forEach((row, index) => {
      const li = document.createElement("li");
      li.className = "leaderboard-item";
      li.innerHTML = `
        <span><span class="leaderboard-rank">#${index + 1}</span> ${row.playerName}</span>
        <strong>${row.wins} win(s)</strong>
      `;
      menuLeaderboardList.appendChild(li);
    });
  } catch {
    menuLeaderboardList.innerHTML = '<li class="leaderboard-empty">Could not load leaderboard.</li>';
  }
}

async function startNewRound() {
  newRoundBtn.disabled = true;
  try {
    const res = await fetch("/api/new-round", { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      setResult(data.error || "Could not start a new round right now.", "error");
      return;
    }

    state.currentRoundId = data.roundId;
    state.currentCaps = data.capacities;
    setRoundSubmissionLocked(false);
    roundLabel.textContent = String(state.currentRoundId);
    drawGraph(state.currentCaps);
    setResult(`Round #${state.currentRoundId} started. Enter your max-flow guess.`, "ok", ["Ready for answer"]);
    answerInput.value = "";
  } catch {
    setResult("Could not start a new round right now.", "error");
  } finally {
    newRoundBtn.disabled = false;
  }
}

async function submitAnswer() {
  if (!state.currentRoundId) {
    setResult("Start a new round first.", "warn");
    return;
  }

  if (state.roundSubmitted) {
    setResult("This round already has one submitted answer. Press New Round to try again.", "warn");
    return;
  }

  const answer = Number(answerInput.value);
  if (Number.isNaN(answer)) {
    setResult("Enter a valid number.", "warn");
    return;
  }

  submitBtn.disabled = true;
  try {
    const res = await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        roundId: state.currentRoundId,
        answer,
        playerName: state.playerName,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      setResult(data.error || "Submission failed.", "error");
      return;
    }

    setResult(`Result: ${String(data.result || "unknown").toUpperCase()}`, "ok", [
      `Correct max flow: ${data.correctMaxFlow}`,
      `Ford-Fulkerson: ${data.fordFulkersonMs} ms`,
      `Edmonds-Karp: ${data.edmondsKarpMs} ms`,
      "One answer saved for this round",
    ]);

    setRoundSubmissionLocked(true);
    recordRecentResult(data, answer);
    await loadLeaderboard();

    if (state.autoStartAfterSubmit) {
      window.setTimeout(() => {
        startNewRound();
      }, 700);
    }
  } catch {
    setResult("Submission failed due to a network error.", "error");
  } finally {
    submitBtn.disabled = state.roundSubmitted;
    answerInput.disabled = state.roundSubmitted;
  }
}

function enterGame() {
  const name = (menuPlayerNameInput.value || "").trim();
  if (!name) {
    menuValidation.classList.remove("hidden");
    return;
  }

  menuValidation.classList.add("hidden");
  state.playerName = name;
  activePlayerLabel.textContent = state.playerName;
  showGame();
  clearRoundView();

  if (state.autoStartEnter) {
    startNewRound();
  }
}

function applySettings() {
  state.autoStartEnter = Boolean(autoStartEnterInput.checked);
  state.autoStartAfterSubmit = Boolean(autoStartAfterSubmitInput.checked);
  closeModal(settingsModal);
}

function openInstructions() {
  openModal(instructionsModal);
}

function openSettings() {
  autoStartEnterInput.checked = state.autoStartEnter;
  autoStartAfterSubmitInput.checked = state.autoStartAfterSubmit;
  openModal(settingsModal);
}

startGameBtn.addEventListener("click", enterGame);
toggleLeaderboardBtn.addEventListener("click", toggleLeaderboard);
toggleRecentResultsBtn.addEventListener("click", toggleRecentResults);
menuBtn.addEventListener("click", showMenu);
backToHubFromMenuBtn.addEventListener("click", backToHub);
resetBoardBtn.addEventListener("click", clearRoundView);

openInstructionsBtn.addEventListener("click", openInstructions);
closeInstructionsBtn.addEventListener("click", () => closeModal(instructionsModal));

openSettingsBtn.addEventListener("click", openSettings);
closeSettingsBtn.addEventListener("click", applySettings);

instructionsModal.addEventListener("click", (event) => {
  if (event.target === instructionsModal) {
    closeModal(instructionsModal);
  }
});

settingsModal.addEventListener("click", (event) => {
  if (event.target === settingsModal) {
    closeModal(settingsModal);
  }
});

newRoundBtn.addEventListener("click", startNewRound);
submitBtn.addEventListener("click", submitAnswer);

loadRecentResults();
renderRecentResults();
setLeaderboardVisible(false);
setRecentResultsVisible(false);
loadLeaderboard();
drawGraph({});
showMenu();
