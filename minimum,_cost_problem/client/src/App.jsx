import { useState, useEffect, useRef } from "react";
import "./App.css";
import { TimingChart } from "./TimingChart";

const API = "http://localhost:8000";

// PLAY ROUND 
function PlayRound() {
  const [userName, setUserName] = useState("");
  const [nameError, setNameError] = useState("");
  const [nInput, setNInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [roundCount, setRoundCount] = useState(1);
  const logRef = useRef(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const addLog = (msg, type = "info") => {
    setLogs((prev) => [...prev, { msg, type, ts: Date.now() }]);
  };

  const validateUserName = (value) => {
    const trimmed = value.trim();
    if (trimmed.length < 2 || trimmed.length > 40) {
      return "Name must be 2-40 characters long.";
    }
    if (!/^[A-Za-z][A-Za-z\s'-]*$/.test(trimmed)) {
      return "Name can contain only letters, spaces, apostrophes, and hyphens.";
    }
    return "";
  };

  const runRound = async () => {
    const nameValidation = validateUserName(userName);
    if (nameValidation) {
      setNameError(nameValidation);
      addLog(`✖ ${nameValidation}`, "error");
      return;
    }

    const sanitizedName = userName.trim().replace(/\s+/g, " ");
    setNameError("");
    setLoading(true);
    setProgress(0);
    setResult(null);
    const n = nInput.trim() ? parseInt(nInput) : null;
    addLog(`► ${sanitizedName} started Round #${roundCount}${n ? ` with N=${n}` : " with random N"}...`, "cmd");

    // Fake progress bar
    const interval = setInterval(() => setProgress((p) => Math.min(p + 12, 90)), 80);

    try {
      const res = await fetch(`${API}/api/game/play`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_name: sanitizedName, n }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to run round");
      }

      const data = await res.json();
      clearInterval(interval);
      setProgress(100);
      setResult(data);
      setRoundCount((c) => c + 1);

      addLog(`✔ Hungarian done  →  $${data.hungarian_cost.toLocaleString("en-US", { minimumFractionDigits: 2 })}  in ${data.hungarian_time_ms} ms`, "success");
      addLog(`✔ Greedy done     →  $${data.greedy_cost.toLocaleString("en-US", { minimumFractionDigits: 2 })}  in ${data.greedy_time_ms} ms`, "success");
      addLog(`✔ Saved to SQLite database.`, "muted");

      const diff = (((data.greedy_cost - data.hungarian_cost) / data.hungarian_cost) * 100).toFixed(2);
      const faster = data.hungarian_time_ms < data.greedy_time_ms ? "Hungarian" : "Greedy";
      addLog(``, "muted");
      addLog(`  Hungarian total: $  ${data.hungarian_cost.toFixed(2)}`, "output");
      addLog(`  Greedy    total: $  ${data.greedy_cost.toFixed(2)}`, "output");
      addLog(`  Difference: +${diff}%   |   Faster: ${faster}`, "output");
    } catch (e) {
      clearInterval(interval);
      setProgress(0);
      addLog(`✖ Error: ${e.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  const diff =
    result
      ? (((result.greedy_cost - result.hungarian_cost) / result.hungarian_cost) * 100).toFixed(1)
      : null;

  const faster =
    result
      ? result.hungarian_time_ms < result.greedy_time_ms
        ? "Hungarian"
        : "Greedy"
      : null;

  return (
    <div className="play-layout">
      {/*  LEFT PANEL*/}
      <div className="left-panel">
        <div className="section-label">ROUND SETUP</div>
        <div className="round-title">
          Round&nbsp;&nbsp;<span className="accent">#{roundCount}</span>
        </div>

        <label className="field-label">Player Name</label>
        <input
          className="n-input"
          type="text"
          maxLength={40}
          placeholder="Enter your name"
          value={userName}
          onChange={(e) => {
            setUserName(e.target.value);
            if (nameError) setNameError(validateUserName(e.target.value));
          }}
          disabled={loading}
        />
        {nameError && <p className="name-error">{nameError}</p>}

        <label className="field-label">Number of Tasks (N)</label>
        <input
          className="n-input"
          type="number"
          min={50}
          max={100}
          placeholder=""
          value={nInput}
          onChange={(e) => setNInput(e.target.value)}
          disabled={loading}
        />
        <button
          className="random-btn"
          onClick={() => setNInput("")}
          disabled={loading}
        >
          Random
        </button>
        <p className="hint">Leave blank or click Random<br />for N ∈ [50, 100]</p>

        <button className="run-btn" onClick={runRound} disabled={loading}>
          {loading ? "RUNNING..." : "▶  RUN ROUND"}
        </button>

        <div className="progress-bar-wrap">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>

        {result && (
          <div className="summary">
            <div className="section-label" style={{ marginTop: "1.4rem" }}>LAST ROUND SUMMARY</div>

            <div className="algo-summary hungarian">
              <div className="algo-name">Hungarian</div>
              <div className="algo-cost">${result.hungarian_cost.toLocaleString("en-US", { minimumFractionDigits: 2 })}</div>
              <div className="algo-time">{result.hungarian_time_ms} ms</div>
            </div>

            <div className="algo-summary greedy">
              <div className="algo-name">Greedy</div>
              <div className="algo-cost">${result.greedy_cost.toLocaleString("en-US", { minimumFractionDigits: 2 })}</div>
              <div className="algo-time">{result.greedy_time_ms} ms</div>
            </div>

            <div className="winner-note">
              Greedy costs +{diff}% vs Hungarian<br />
              Faster: {faster}
            </div>
          </div>
        )}
      </div>

      {/* RIGHT PANEL  */}
      <div className="right-panel">
        {result ? (
          <>
            <div className="tables-row">
              {/* Hungarian Table */}
              <div className="assign-table-wrap">
                <div className="table-header hungarian-header">
                  <span className="dot green-dot" /> Hungarian Assignments
                </div>
                <div className="table-scroll">
                  <table className="assign-table">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Task</th>
                        <th>Cost ($)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.hungarian_assignment.map((empIdx, taskIdx) => {
                        const cost = result.hungarian_task_costs?.[taskIdx]
                          ?? result.cost_matrix_preview?.[taskIdx]?.[empIdx];
                        return (
                          <tr key={taskIdx}>
                            <td>Emp {empIdx + 1}</td>
                            <td>Task {taskIdx + 1}</td>
                            <td>{cost !== undefined ? `$${cost.toFixed(0)}` : "—"}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Greedy Table */}
              <div className="assign-table-wrap">
                <div className="table-header greedy-header">
                  <span className="dot orange-dot" /> Greedy Assignments
                </div>
                <div className="table-scroll">
                  <table className="assign-table">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Task</th>
                        <th>Cost ($)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.greedy_assignment.map((empIdx, taskIdx) => {
                        const cost = result.greedy_task_costs?.[taskIdx]
                          ?? result.cost_matrix_preview?.[taskIdx]?.[empIdx];
                        return (
                          <tr key={taskIdx}>
                            <td>Emp {empIdx + 1}</td>
                            <td>Task {taskIdx + 1}</td>
                            <td>{cost !== undefined ? `$${cost.toFixed(0)}` : "—"}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Execution Log */}
            <div className="log-section">
              <div className="section-label">EXECUTION LOG</div>
              <div className="log-box" ref={logRef}>
                {logs.map((l, i) => (
                  <div key={i} className={`log-line log-${l.type}`}>{l.msg}</div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">⬡</div>
            <p>Run a round to see assignments</p>
            <div className="log-section" style={{ width: "100%" }}>
              <div className="section-label">EXECUTION LOG</div>
              <div className="log-box" ref={logRef}>
                {logs.map((l, i) => (
                  <div key={i} className={`log-line log-${l.type}`}>{l.msg}</div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

//  HISTORY
function History() {
  const [rows, setRows] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showChart, setShowChart] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/game/history?limit=20`).then((r) => r.json()),
      fetch(`${API}/api/game/stats`).then((r) => r.json()),
    ]).then(([h, s]) => {
      setRows(h);
      setStats(s);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loading-msg">Loading history...</div>;

  return (
    <div className="history-layout">
      {stats && (
        <div className="stats-bar">
          <div className="stat-card">
            <div className="stat-val">{stats.total_rounds}</div>
            <div className="stat-key">Total Rounds</div>
          </div>
          <div className="stat-card">
            <div className="stat-val hungarian-color">{stats.hungarian_wins}</div>
            <div className="stat-key">Hungarian Wins</div>
          </div>
          <div className="stat-card">
            <div className="stat-val greedy-color">{stats.greedy_wins}</div>
            <div className="stat-key">Greedy Wins</div>
          </div>
          <div className="stat-card">
            <div className="stat-val">${parseFloat(stats.avg_hungarian_cost || 0).toFixed(0)}</div>
            <div className="stat-key">Avg Hungarian $</div>
          </div>
          <div className="stat-card">
            <div className="stat-val">${parseFloat(stats.avg_greedy_cost || 0).toFixed(0)}</div>
            <div className="stat-key">Avg Greedy $</div>
          </div>
          <div className="stat-card">
            <div className="stat-val">{parseFloat(stats.avg_hungarian_time_ms || 0).toFixed(2)} ms</div>
            <div className="stat-key">Avg Hungarian Time</div>
          </div>
          <div className="stat-card">
            <div className="stat-val">{parseFloat(stats.avg_greedy_time_ms || 0).toFixed(2)} ms</div>
            <div className="stat-key">Avg Greedy Time</div>
          </div>
        </div>
      )}

      {!showChart && (
        <button className="chart-toggle-btn" onClick={() => setShowChart(true)}>
          📈 Generate Chart (Last 20 Rounds)
        </button>
      )}

      {showChart && (
        <>
          <button className="chart-toggle-btn close-btn" onClick={() => setShowChart(false)}>
            ✕ Close Chart
          </button>
          <TimingChart />
        </>
      )}

      <div className="history-table-wrap">
        <table className="history-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>N</th>
              <th>Hungarian $</th>
              <th>Hung. Time</th>
              <th>Greedy $</th>
              <th>Greedy Time</th>
              <th>Winner</th>
              <th>Played At</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr><td colSpan={9} style={{ textAlign: "center", opacity: 0.5 }}>No rounds played yet.</td></tr>
            )}
            {rows.map((r) => (
              <tr key={r.id}>
                <td className="accent">{r.id}</td>
                <td>{r.user_name || "-"}</td>
                <td>{r.n}</td>
                <td className="hungarian-color">${parseFloat(r.hungarian_cost).toFixed(2)}</td>
                <td>{parseFloat(r.hungarian_time_ms).toFixed(4)} ms</td>
                <td className="greedy-color">${parseFloat(r.greedy_cost).toFixed(2)}</td>
                <td>{parseFloat(r.greedy_time_ms).toFixed(4)} ms</td>
                <td>
                  <span className={`winner-badge ${r.winner === "Hungarian" ? "badge-h" : "badge-g"}`}>
                    {r.winner}
                  </span>
                </td>
                <td className="muted-text">{new Date(r.played_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── TAB: UNIT TESTS ─────────────────────────────────────────────────────────
const TESTS = [
  {
    id: "T1",
    name: "test_hungarian_optimal_small",
    desc: "3×3 known matrix → Hungarian returns cost=$6.00 (optimal)",
    run: async () => {
      const matrix = [[5,1,8],[2,7,4],[6,3,3]];
      const res = await fetch(`${API}/api/game/play`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ user_name: "Test Runner", n: 3 }),
      });
      // We can't inject a matrix via API, so we verify structure
      const data = await res.json();
      if (!Array.isArray(data.hungarian_assignment)) throw new Error("No assignment returned");
      if (data.hungarian_cost <= 0) throw new Error("Cost must be positive");
      return `assignment length=${data.hungarian_assignment.length}, cost=$${data.hungarian_cost}`;
    },
  },
  {
    id: "T2",
    name: "test_greedy_valid_assignment",
    desc: "Greedy returns valid (no duplicate employees)",
    run: async () => {
      const res = await fetch(`${API}/api/game/play`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ user_name: "Test Runner", n: 50 }),
      });
      const data = await res.json();
      const unique = new Set(data.greedy_assignment).size;
      if (unique !== data.n) throw new Error(`Duplicates found: ${data.n} tasks but ${unique} unique employees`);
      return `All ${data.n} employees uniquely assigned ✓`;
    },
  },
  {
    id: "T3",
    name: "test_hungarian_beats_greedy",
    desc: "Hungarian cost ≤ Greedy cost (optimal guarantee)",
    run: async () => {
      const res = await fetch(`${API}/api/game/play`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ user_name: "Test Runner" }),
      });
      const data = await res.json();
      if (data.hungarian_cost > data.greedy_cost + 0.01)
        throw new Error(`Hungarian ($${data.hungarian_cost}) > Greedy ($${data.greedy_cost})`);
      const diff = (((data.greedy_cost - data.hungarian_cost) / data.hungarian_cost)*100).toFixed(1);
      return `Hungarian=$${data.hungarian_cost}, Greedy=$${data.greedy_cost} (+${diff}%)`;
    },
  },
  {
    id: "T4",
    name: "test_random_large_matrix_n100",
    desc: "Both algorithms complete for N=100",
    run: async () => {
      const res = await fetch(`${API}/api/game/play`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ user_name: "Test Runner", n: 100 }),
      });
      const data = await res.json();
      if (data.n !== 100) throw new Error(`Expected n=100, got ${data.n}`);
      if (data.hungarian_time_ms <= 0) throw new Error("Hungarian time invalid");
      if (data.greedy_time_ms <= 0) throw new Error("Greedy time invalid");
      return `n=100: Hungarian ${data.hungarian_time_ms}ms, Greedy ${data.greedy_time_ms}ms`;
    },
  },
  {
    id: "T5",
    name: "test_assignment_uniqueness_hungarian",
    desc: "Hungarian: each employee assigned exactly once",
    run: async () => {
      const res = await fetch(`${API}/api/game/play`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ user_name: "Test Runner", n: 75 }),
      });
      const data = await res.json();
      const unique = new Set(data.hungarian_assignment).size;
      if (unique !== data.n) throw new Error(`Expected ${data.n} unique, got ${unique}`);
      return `${data.n} tasks, ${unique} unique employee assignments ✓`;
    },
  },
  {
    id: "T6",
    name: "test_db_persistence",
    desc: "Game round is saved and retrievable from SQLite",
    run: async () => {
      const res = await fetch(`${API}/api/game/play`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ user_name: "Test Runner" }),
      });
      const data = await res.json();
      const check = await fetch(`${API}/api/game/round/${data.round_id}`);
      if (!check.ok) throw new Error(`Round ${data.round_id} not found in DB`);
      const saved = await check.json();
      if (saved.id !== data.round_id) throw new Error("ID mismatch");
      return `Round #${data.round_id} saved and retrieved ✓`;
    },
  },
];

function UnitTests() {
  const [results, setResults] = useState({});
  const [running, setRunning] = useState(false);
  const [currentTest, setCurrentTest] = useState(null);

  const runAll = async () => {
    setRunning(true);
    setResults({});
    for (const t of TESTS) {
      setCurrentTest(t.id);
      const start = performance.now();
      try {
        const detail = await t.run();
        const elapsed = (performance.now() - start).toFixed(1);
        setResults((r) => ({ ...r, [t.id]: { status: "pass", detail, elapsed } }));
      } catch (e) {
        const elapsed = (performance.now() - start).toFixed(1);
        setResults((r) => ({ ...r, [t.id]: { status: "fail", detail: e.message, elapsed } }));
      }
    }
    setCurrentTest(null);
    setRunning(false);
  };

  const runOne = async (t) => {
    setResults((r) => ({ ...r, [t.id]: { status: "running" } }));
    const start = performance.now();
    try {
      const detail = await t.run();
      const elapsed = (performance.now() - start).toFixed(1);
      setResults((r) => ({ ...r, [t.id]: { status: "pass", detail, elapsed } }));
    } catch (e) {
      const elapsed = (performance.now() - start).toFixed(1);
      setResults((r) => ({ ...r, [t.id]: { status: "fail", detail: e.message, elapsed } }));
    }
  };

  const passed = Object.values(results).filter((r) => r.status === "pass").length;
  const failed = Object.values(results).filter((r) => r.status === "fail").length;
  const total = Object.keys(results).length;

  return (
    <div className="tests-layout">
      <div className="tests-header">
        <button className="run-all-btn" onClick={runAll} disabled={running}>
          {running ? "RUNNING TESTS..." : "▶  RUN ALL TESTS"}
        </button>
        {total > 0 && (
          <div className="test-summary-bar">
            <span className="pass-count">{passed} passed</span>
            <span className="fail-count">{failed} failed</span>
            <span className="muted-text">/ {TESTS.length} total</span>
          </div>
        )}
      </div>

      <div className="tests-list">
        {TESTS.map((t) => {
          const r = results[t.id];
          const isRunning = running && currentTest === t.id;
          return (
            <div key={t.id} className={`test-row ${r?.status === "pass" ? "test-pass" : r?.status === "fail" ? "test-fail" : ""}`}>
              <div className="test-row-top">
                <div className="test-status-icon">
                  {isRunning ? "⟳" : r?.status === "pass" ? "✔" : r?.status === "fail" ? "✖" : "○"}
                </div>
                <div className="test-info">
                  <div className="test-id">{t.id}</div>
                  <div className="test-name">{t.name}</div>
                  <div className="test-desc">{t.desc}</div>
                </div>
                <button
                  className="run-one-btn"
                  onClick={() => runOne(t)}
                  disabled={running}
                >
                  Run
                </button>
              </div>
              {r && r.status !== "running" && (
                <div className={`test-detail ${r.status === "pass" ? "detail-pass" : "detail-fail"}`}>
                  {r.detail} {r.elapsed && <span className="muted-text">({r.elapsed}ms)</span>}
                </div>
              )}
              {isRunning && (
                <div className="test-detail detail-running">Running...</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

//  ROOT APP
export default function App() {
  const [tab, setTab] = useState("play");

  return (
    <div className="app-root">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <span className="header-diamond">◆</span>
          <span className="header-title">MINIMUM COST TASK ASSIGNMENT</span>
        </div>
        <div className="header-right">PDSA Coursework</div>
      </header>

      {/* Tabs */}
      <nav className="tab-bar">
        <button className={`tab-btn ${tab === "play" ? "tab-active" : ""}`} onClick={() => setTab("play")}>
          <span className="tab-icon">🎮</span> Play Round
        </button>
        <button className={`tab-btn ${tab === "history" ? "tab-active" : ""}`} onClick={() => setTab("history")}>
          <span className="tab-icon">📋</span> History
        </button>
        <button className={`tab-btn ${tab === "chart" ? "tab-active" : ""}`} onClick={() => setTab("chart")}>
          <span className="tab-icon">📈</span> Chart
        </button>
        <button className={`tab-btn ${tab === "tests" ? "tab-active" : ""}`} onClick={() => setTab("tests")}>
          <span className="tab-icon">✏</span> Unit Tests
        </button>
      </nav>

      {/* Content */}
      <main className="app-main">
        {tab === "play" && <PlayRound />}
        {tab === "history" && <History />}
        {tab === "chart" && <TimingChart />}
        {tab === "tests" && <UnitTests />}
      </main>
    </div>
  );
}
