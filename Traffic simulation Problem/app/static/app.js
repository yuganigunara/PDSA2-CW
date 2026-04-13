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
  ["D", "H"],
  ["E", "G"],
  ["E", "H"],
  ["F", "G"],
  ["F", "H"],
  ["G", "T"],
  ["H", "T"],
];

const labelOffsets = {
  "B->F": { dx: -10, dy: -10 },
  "C->E": { dx: 10, dy: 6 },
  "D->F": { dx: -12, dy: 10 },
  "E->H": { dx: 10, dy: -8 },
  "F->G": { dx: -8, dy: 8 },
  "F->H": { dx: 0, dy: 12 },
};

let currentRoundId = null;
let currentCaps = {};

const svg = document.getElementById("network");
const newRoundBtn = document.getElementById("newRoundBtn");
const submitBtn = document.getElementById("submitBtn");
const answerInput = document.getElementById("answer");
const resultBox = document.getElementById("resultBox");
const playerNameInput = document.getElementById("playerName");
const leaderboardList = document.getElementById("leaderboardList");

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
  const res = await fetch("/api/leaderboard");
  const rows = await res.json();
  leaderboardList.innerHTML = "";

  if (rows.length === 0) {
    leaderboardList.innerHTML = '<li class="leaderboard-empty">No winners yet.</li>';
    return;
  }

  rows.forEach((row, index) => {
    const li = document.createElement("li");
    li.className = "leaderboard-item";
    li.innerHTML = `
      <span><span class="leaderboard-rank">#${index + 1}</span> ${row.playerName}</span>
      <strong>${row.wins} win(s)</strong>
    `;
    leaderboardList.appendChild(li);
  });
}

async function startNewRound() {
  newRoundBtn.disabled = true;
  try {
    const res = await fetch("/api/new-round", { method: "POST" });
    const data = await res.json();
    currentRoundId = data.roundId;
    currentCaps = data.capacities;
    drawGraph(currentCaps);
    setResult(`Round #${currentRoundId} started. Enter your max-flow guess.`, "ok", ["Ready for answer"]);
    answerInput.value = "";
  } catch {
    setResult("Could not start a new round right now.", "error");
  } finally {
    newRoundBtn.disabled = false;
  }
}

async function submitAnswer() {
  if (!currentRoundId) {
    setResult("Start a new round first.", "warn");
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
        roundId: currentRoundId,
        answer,
        playerName: playerNameInput.value,
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
    ]);

    await loadLeaderboard();
  } catch {
    setResult("Submission failed due to a network error.", "error");
  } finally {
    submitBtn.disabled = false;
  }
}

newRoundBtn.addEventListener("click", startNewRound);
submitBtn.addEventListener("click", submitAnswer);

loadLeaderboard();
drawGraph({});
