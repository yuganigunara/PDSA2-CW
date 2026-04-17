import React, { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = "http://127.0.0.1:8003/api/sixteen-queens";
const KNOWN_ANSWER = 14772512;
const FALLBACK_BOARD = [
  "Q...............",
  "..Q.............",
  "....Q...........",
  ".Q..............",
  "............Q...",
  "........Q.......",
  ".............Q..",
  "...........Q....",
  "..............Q.",
  ".....Q..........",
  "...............Q",
  "......Q.........",
  "...Q............",
  "..........Q.....",
  ".......Q........",
  ".........Q......",
];

const formatMs = (timeNs) => `${(Number(timeNs || 0) / 1e6).toFixed(2)} ms`;
const formatKb = (bytes) => `${(Number(bytes || 0) / 1024).toFixed(1)} KB`;

export default function App() {
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [playerName, setPlayerName] = useState("");
  const [answer, setAnswer] = useState(String(KNOWN_ANSWER));
  const [roundsScroll, setRoundsScroll] = useState(0);
  const [answersScroll, setAnswersScroll] = useState(0);
  const seededRef = useRef(false);
  const roundsTableRef = useRef(null);
  const answersTableRef = useRef(null);

  async function loadState() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(API_BASE);
      if (!response.ok) {
        throw new Error("Could not load Sixteen Queens data.");
      }
      setState(await response.json());
    } catch (fetchError) {
      setError(fetchError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadState();
  }, []);

  useEffect(() => {
    if (loading || seededRef.current) {
      return;
    }

    const hasRounds = Boolean(state?.dashboard?.rounds?.length);
    if (!hasRounds) {
      seededRef.current = true;
      runBenchmark(1);
    }
  }, [loading, state]);

  const rounds = useMemo(() => {
    const map = new Map();
    for (const row of state?.dashboard?.rounds || []) {
      const item = map.get(row.round_no) || { round_no: row.round_no };
      item[row.algorithm] = row;
      map.set(row.round_no, item);
    }
    return [...map.values()].slice(-10);
  }, [state]);

  const maxTime = useMemo(() => {
    const values = rounds.flatMap((row) => [row.sequential?.time_ns || 0, row.threaded?.time_ns || 0]);
    return Math.max(1, ...values);
  }, [rounds]);

  async function runBenchmark(count) {
    setRunning(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch(`${API_BASE}/benchmark?count=${count}`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Benchmark failed.");
      }
      setMessage(data.message);
      await loadState();
    } catch (benchError) {
      setError(benchError.message);
    } finally {
      setRunning(false);
    }
  }

  async function submitAnswer(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const response = await fetch(`${API_BASE}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_name: playerName, answer: Number(answer) }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Answer rejected.");
      }
      setMessage(data.message);
      setPlayerName("");
      setAnswer(String(KNOWN_ANSWER));
      await loadState();
    } catch (submitError) {
      setError(submitError.message);
    }
  }

  const sampleBoard = state?.sample_board?.length ? state.sample_board : FALLBACK_BOARD;
  const recentAnswers = state?.dashboard?.answers || [];
  const dbRounds = state?.dashboard?.rounds || [];

  useEffect(() => {
    const el = roundsTableRef.current;
    if (!el) return;
    const max = Math.max(0, el.scrollHeight - el.clientHeight);
    el.scrollTop = (roundsScroll / 100) * max;
  }, [roundsScroll, dbRounds.length]);

  useEffect(() => {
    const el = answersTableRef.current;
    if (!el) return;
    const max = Math.max(0, el.scrollHeight - el.clientHeight);
    el.scrollTop = (answersScroll / 100) * max;
  }, [answersScroll, recentAnswers.length]);

  return (
    <div className="queens-page">
      <header className="queens-hero">
        <div>
          <p className="eyebrow">Sixteen Queens Puzzle</p>
          <h1>Sequential vs Threaded Benchmark Arena</h1>
          <p className="subcopy">A 16x16 board, backtracking benchmark, and sqlite-backed chart for your report.</p>
        </div>
        <div className="hero-actions">
          <button onClick={() => runBenchmark(1)} disabled={running}>Run 1 Round</button>
          <button onClick={() => runBenchmark(20)} disabled={running}>Run 20 Tests</button>
        </div>
      </header>

      {loading && <div className="banner">Loading puzzle state...</div>}
      {error && <div className="banner banner-error">{error}</div>}
      {message && <div className="banner banner-ok">{message}</div>}

      <section className="queens-grid">
        <article className="panel board-panel">
          <div className="panel-head">
            <h2>Sample Board</h2>
            <span className="chip">{state?.size || 16} x {state?.size || 16}</span>
          </div>
          <div className="board">
            {sampleBoard.map((row, rowIndex) =>
              row.split("").map((cell, colIndex) => (
                <div key={`${rowIndex}-${colIndex}`} className={`cell ${(rowIndex + colIndex) % 2 === 0 ? "light" : "dark"} ${cell === "Q" ? "queen" : ""}`}>
                  {cell === "Q" ? "Q" : ""}
                </div>
              ))
            )}
          </div>
        </article>

        <article className="panel control-panel">
          <div className="panel-head">
            <h2>Player Answer</h2>
            <span className="chip accent">Known answer: {KNOWN_ANSWER.toLocaleString()}</span>
          </div>

          <form className="answer-form" onSubmit={submitAnswer}>
            <label>Player Name<input value={playerName} onChange={(event) => setPlayerName(event.target.value)} placeholder="Enter your name" /></label>
            <label>Your Answer<input value={answer} onChange={(event) => setAnswer(event.target.value)} inputMode="numeric" /></label>
            <div className="form-actions">
              <button type="submit">Submit Answer</button>
              <button type="button" className="outline" onClick={loadState}>Refresh Data</button>
            </div>
          </form>

          <div className="stats-grid">
            <div><strong>{recentAnswers.length}</strong><span>saved answers</span></div>
            <div><strong>{rounds.length}</strong><span>rounds charted</span></div>
            <div><strong>{formatMs(rounds.at(-1)?.sequential?.time_ns)}</strong><span>latest seq time</span></div>
            <div><strong>{formatMs(rounds.at(-1)?.threaded?.time_ns)}</strong><span>latest threaded time</span></div>
          </div>
        </article>
      </section>

      <section className="panel chart-panel">
        <div className="panel-head">
          <h2>Benchmark Chart</h2>
          <span className="chip">Top 10 rounds from sqlite</span>
        </div>
        {!rounds.length && !loading && (
          <div className="banner banner-ok">No benchmark data yet. Loading a sample round to seed the sqlite chart.</div>
        )}
        <div className="chart-list">
          {rounds.map((round) => (
            <div className="chart-row" key={round.round_no}>
              <span className="round-tag">Round {round.round_no}</span>
              <div className="bar-group">
                {round.sequential && (
                  <div className="bar-line">
                    <small>Sequential</small>
                    <div className="bar-track"><span style={{ width: `${(round.sequential.time_ns / maxTime) * 100}%` }} /></div>
                    <span>{formatMs(round.sequential.time_ns)} | {formatKb(round.sequential.peak_bytes)}</span>
                  </div>
                )}
                {round.threaded && (
                  <div className="bar-line">
                    <small>Threaded</small>
                    <div className="bar-track threaded"><span style={{ width: `${(round.threaded.time_ns / maxTime) * 100}%` }} /></div>
                    <span>{formatMs(round.threaded.time_ns)} | {formatKb(round.threaded.peak_bytes)}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel db-panel">
        <div className="panel-head">
          <h2>SQLite Data</h2>
          <span className="chip">Live rows from database</span>
        </div>

        <div className="db-grid">
          <article className="db-card">
            <h3>Benchmark Rounds</h3>
            <div className="scroll-controls">
              <span>Total rows: {dbRounds.length}</span>
              <input type="range" min="0" max="100" value={roundsScroll} onChange={(event) => setRoundsScroll(Number(event.target.value))} />
            </div>
            <div className="db-table-wrap" ref={roundsTableRef}>
              <table className="db-table">
                <thead>
                  <tr>
                    <th>Round</th>
                    <th>Algo</th>
                    <th>Solutions</th>
                    <th>Time</th>
                    <th>Peak</th>
                  </tr>
                </thead>
                <tbody>
                  {dbRounds.map((row, index) => (
                    <tr key={`${row.round_no}-${row.algorithm}-${index}`}>
                      <td>{row.round_no}</td>
                      <td>{row.algorithm}</td>
                      <td>{Number(row.solutions || 0).toLocaleString()}</td>
                      <td>{formatMs(row.time_ns)}</td>
                      <td>{formatKb(row.peak_bytes)}</td>
                    </tr>
                  ))}
                  {!dbRounds.length && (
                    <tr>
                      <td colSpan="5">No benchmark rows in sqlite yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </article>

          <article className="db-card">
            <h3>Recognized Answers</h3>
            <div className="scroll-controls">
              <span>Total rows: {recentAnswers.length}</span>
              <input type="range" min="0" max="100" value={answersScroll} onChange={(event) => setAnswersScroll(Number(event.target.value))} />
            </div>
            <div className="db-table-wrap" ref={answersTableRef}>
              <table className="db-table">
                <thead>
                  <tr>
                    <th>Round</th>
                    <th>Player</th>
                    <th>Answer</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {recentAnswers.map((row, index) => (
                    <tr key={`${row.round_no}-${row.player_name}-${index}`}>
                      <td>{row.round_no}</td>
                      <td>{row.player_name}</td>
                      <td>{Number(row.answer || 0).toLocaleString()}</td>
                      <td>{String(row.created_at || "").replace("T", " ").slice(0, 19)}</td>
                    </tr>
                  ))}
                  {!recentAnswers.length && (
                    <tr>
                      <td colSpan="4">No answer rows in sqlite yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </article>
        </div>
      </section>
    </div>
  );
}
