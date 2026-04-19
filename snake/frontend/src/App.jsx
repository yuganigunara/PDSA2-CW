import { useEffect, useMemo, useState } from "react";
import snakeImage from "./assets/snake-illustration.svg";

function nsToMs(ns) {
  return Number((ns / 1_000_000).toFixed(3));
}

async function parseResponsePayload(response) {
  const raw = await response.text();
  if (!raw || !raw.trim()) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    return { detail: raw };
  }
}

function BoardGrid({ board }) {
  if (!board) {
    return null;
  }

  const { size, goal, ladders, snakes } = board;
  const cells = Array.from({ length: goal }, (_, i) => i + 1);
  const rows = [];
  for (let row = size - 1; row >= 0; row -= 1) {
    const start = row * size + 1;
    const rowCells = cells.slice(start - 1, start - 1 + size);
    const serpentine = ((size - 1 - row) % 2 === 0) ? rowCells : rowCells.slice().reverse();
    rows.push(...serpentine);
  }

  const ladderStarts = new Set(Object.keys(ladders).map((k) => Number(k)));
  const snakeStarts = new Set(Object.keys(snakes).map((k) => Number(k)));
  const cellSize = 100 / size;
  const cellCenters = new Map();

  rows.forEach((cell, index) => {
    const rowIndex = Math.floor(index / size);
    const colIndex = index % size;
    cellCenters.set(cell, {
      x: (colIndex + 0.5) * cellSize,
      y: (rowIndex + 0.5) * cellSize,
    });
  });

  const ladderDrawings = Object.entries(ladders).map(([startRaw, endRaw]) => {
    const start = Number(startRaw);
    const end = Number(endRaw);
    const from = cellCenters.get(start);
    const to = cellCenters.get(end);
    if (!from || !to) {
      return null;
    }

    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const len = Math.hypot(dx, dy) || 1;
    const railGap = Math.max(1.2, Math.min(2.8, len * 0.08));
    const rungCount = Math.max(4, Math.floor(len / 6));
    const ux = dx / len;
    const uy = dy / len;
    const px = -uy;
    const py = ux;

    const a1 = { x: from.x + px * railGap, y: from.y + py * railGap };
    const a2 = { x: to.x + px * railGap, y: to.y + py * railGap };
    const b1 = { x: from.x - px * railGap, y: from.y - py * railGap };
    const b2 = { x: to.x - px * railGap, y: to.y - py * railGap };

    return (
      <g key={`ladder-${start}-${end}`}>
        <line className="ladder-rail" x1={a1.x} y1={a1.y} x2={a2.x} y2={a2.y} />
        <line className="ladder-rail" x1={b1.x} y1={b1.y} x2={b2.x} y2={b2.y} />
        {Array.from({ length: rungCount }, (_, i) => {
          const t = (i + 1) / (rungCount + 1);
          const mx = from.x + ux * len * t;
          const my = from.y + uy * len * t;
          return (
            <line
              key={`rung-${start}-${end}-${i}`}
              className="ladder-rung"
              x1={mx + px * railGap}
              y1={my + py * railGap}
              x2={mx - px * railGap}
              y2={my - py * railGap}
            />
          );
        })}
      </g>
    );
  });

  const snakeDrawings = Object.entries(snakes).map(([startRaw, endRaw]) => {
    const start = Number(startRaw);
    const end = Number(endRaw);
    const from = cellCenters.get(start);
    const to = cellCenters.get(end);
    if (!from || !to) {
      return null;
    }

    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const len = Math.hypot(dx, dy) || 1;
    const angle = (Math.atan2(from.y - to.y, from.x - to.x) * 180) / Math.PI;
    const width = Math.max(8, len * 1.05);
    const height = Math.max(3.4, Math.min(7, len * 0.24));
    const cx = (from.x + to.x) / 2;
    const cy = (from.y + to.y) / 2;
    const hue = (start * 29 + end * 17) % 360;

    return (
      <image
        key={`snake-image-${start}-${end}`}
        className="snake-image"
        href={snakeImage}
        x={cx - width / 2}
        y={cy - height / 2}
        width={width}
        height={height}
        preserveAspectRatio="none"
        transform={`rotate(${angle} ${cx} ${cy})`}
        style={{ filter: `drop-shadow(0 0.6px 1.2px rgba(13, 23, 40, 0.45)) hue-rotate(${hue}deg)` }}
      />
    );
  });

  return (
    <div className="board-shell">
      <div className="board-stack">
        <svg className="board-overlay" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          {snakeDrawings}
          {ladderDrawings}
        </svg>

        <div
          className="board-grid"
          style={{ gridTemplateColumns: `repeat(${size}, minmax(34px, 1fr))` }}
          aria-label="Snake and ladder board"
        >
          {rows.map((cell, index) => {
            const rowIndex = Math.floor(index / size);
            const colIndex = index % size;
            const isStart = cell === 1;
            const isGoal = cell === goal;
            const ladderTo = ladders[cell];
            const snakeTo = snakes[cell];
            const isLight = (rowIndex + colIndex) % 2 === 0;
            const tooltip = ladderTo
              ? `Ladder to ${ladderTo}`
              : snakeTo
                ? `Snake to ${snakeTo}`
                : `Cell ${cell}`;

            return (
              <div
                key={cell}
                className={[
                  "cell",
                  isLight ? "cell-check-light" : "cell-check-dark",
                  isStart ? "cell-start" : "",
                  isGoal ? "cell-goal" : "",
                  ladderStarts.has(cell) ? "cell-ladder" : "",
                  snakeStarts.has(cell) ? "cell-snake" : "",
                ].join(" ")}
                title={tooltip}
                aria-label={tooltip}
              >
                <span className="cell-number">{cell}</span>

                {isStart ? <span className="cell-tag start-tag">Start</span> : null}
                {isGoal ? <span className="cell-tag goal-tag">Goal</span> : null}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function DatabaseTables({ dbSnapshot, dbRequested }) {
  return (
    <section className="card db-panel">
      <h2>Database Output</h2>
      {dbSnapshot.players.length ||
      dbSnapshot.games.length ||
      dbSnapshot.game_jumps.length ||
      dbSnapshot.algorithm_runs.length ? (
        <>
          <h3>players</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>player_id</th>
                  <th>player_name</th>
                  <th>created_at</th>
                </tr>
              </thead>
              <tbody>
                {dbSnapshot.players.map((row) => (
                  <tr key={`player-${row.player_id}`}>
                    <td>{row.player_id}</td>
                    <td>{row.player_name}</td>
                    <td>{row.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h3>games</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>game_id</th>
                  <th>player_id</th>
                  <th>board_size</th>
                  <th>correct_answer</th>
                  <th>player_answer</th>
                  <th>is_correct</th>
                  <th>created_at</th>
                </tr>
              </thead>
              <tbody>
                {dbSnapshot.games.map((row) => (
                  <tr key={`game-${row.game_id}`}>
                    <td>{row.game_id}</td>
                    <td>{row.player_id}</td>
                    <td>{row.board_size}</td>
                    <td>{row.correct_answer}</td>
                    <td>{row.player_answer}</td>
                    <td>{row.is_correct}</td>
                    <td>{row.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h3>game_jumps</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>jump_id</th>
                  <th>game_id</th>
                  <th>jump_type</th>
                  <th>start_cell</th>
                  <th>end_cell</th>
                </tr>
              </thead>
              <tbody>
                {dbSnapshot.game_jumps.map((row) => (
                  <tr key={`jump-${row.jump_id}`}>
                    <td>{row.jump_id}</td>
                    <td>{row.game_id}</td>
                    <td>{row.jump_type}</td>
                    <td>{row.start_cell}</td>
                    <td>{row.end_cell}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h3>algorithm_runs</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>run_id</th>
                  <th>game_id</th>
                  <th>algorithm_name</th>
                  <th>minimum_throws</th>
                  <th>time_ns</th>
                </tr>
              </thead>
              <tbody>
                {dbSnapshot.algorithm_runs.map((row) => (
                  <tr key={`run-${row.run_id}`}>
                    <td>{row.run_id}</td>
                    <td>{row.game_id}</td>
                    <td>{row.algorithm_name}</td>
                    <td>{row.minimum_throws}</td>
                    <td>{row.time_ns}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : dbRequested ? (
        <p className="empty">No rows in database yet.</p>
      ) : (
        <p className="empty">Load database output to view all normalized tables.</p>
      )}
    </section>
  );
}

function DatabasePage({ dbSnapshot, dbRequested, dbMessage, loading, onReload, onBack }) {
  return (
    <div className="page">
      <header className="hero card">
        <h1>Database Output</h1>
        <p>Full normalized tables loaded from SQLite.</p>
        <div className="actions db-actions">
          <button type="button" onClick={onBack}>Back To Game</button>
          <button type="button" className="ghost" onClick={onReload} disabled={loading}>Reload Tables</button>
        </div>
        {dbMessage ? <p className="status">{dbMessage}</p> : null}
      </header>

      <DatabaseTables dbSnapshot={dbSnapshot} dbRequested={dbRequested} />
    </div>
  );
}

function App() {
  const [playerName, setPlayerName] = useState("");
  const [boardSize, setBoardSize] = useState(8);
  const [round, setRound] = useState(null);
  const [selected, setSelected] = useState(null);
  const [resultMessage, setResultMessage] = useState("Welcome. Start a round to play.");
  const [benchmark, setBenchmark] = useState(null);
  const [benchmarkRequested, setBenchmarkRequested] = useState(false);
  const [dbSnapshot, setDbSnapshot] = useState({
    players: [],
    games: [],
    game_jumps: [],
    algorithm_runs: [],
  });
  const [dbRequested, setDbRequested] = useState(false);
  const [dbMessage, setDbMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [answerPopup, setAnswerPopup] = useState(null);
  const [view, setView] = useState(() => (window.location.hash === "#database" ? "database" : "game"));

  useEffect(() => {
    const handleHashChange = () => {
      setView(window.location.hash === "#database" ? "database" : "game");
    };
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const normalizeDatabaseSnapshot = (payload) => ({
    players: Array.isArray(payload?.players) ? payload.players : [],
    games: Array.isArray(payload?.games) ? payload.games : [],
    game_jumps: Array.isArray(payload?.game_jumps) ? payload.game_jumps : [],
    algorithm_runs: Array.isArray(payload?.algorithm_runs) ? payload.algorithm_runs : [],
  });

  const avg = useMemo(() => {
    if (!benchmark || !benchmark.samples?.length) {
      return { bfs: 0, dp: 0, maxMs: 1 };
    }
    const bfs = benchmark.average_bfs_ms;
    const dp = benchmark.average_dp_ms;
    const maxMs = Math.max(...benchmark.samples.map((s) => Math.max(s.bfs_ms, s.dp_ms)), 1);
    return { bfs, dp, maxMs };
  }, [benchmark]);

  const startRound = async () => {
    setLoading(true);
    setSelected(null);
    setResultMessage("");

    try {
      const response = await fetch("/api/round", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          player_name: playerName,
          board_size: Number(boardSize),
        }),
      });

      const payload = await parseResponsePayload(response);
      if (!response.ok) {
        throw new Error(payload?.detail || `Could not start round (HTTP ${response.status}).`);
      }

      setRound(payload);
      setResultMessage("Round ready. Pick your minimum throws answer.");
    } catch (error) {
      const text =
        error instanceof TypeError
          ? "Backend is offline. Start FastAPI on 127.0.0.1:8000 and try again."
          : error.message;
      setResultMessage(text);
      setRound(null);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!round) {
      setResultMessage("Start a round first.");
      return;
    }

    if (selected === null) {
      setResultMessage("Select an option before submitting.");
      return;
    }

    if (round.outcome === "DRAW") {
      setResultMessage("DRAW: BFS and DP disagreed for this board. Start a new round.");
      return;
    }

    if (selected !== round.correct_answer) {
      setResultMessage(`LOSE: correct answer is ${round.correct_answer}. Try a new round.`);
      setAnswerPopup({
        tone: "error",
        title: "Wrong Answer",
        message: `Your answer is incorrect. Correct answer is ${round.correct_answer}.`,
      });
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/api/results", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          player_name: round.player_name,
          answer: selected,
          correct_answer: round.correct_answer,
          outcome: round.outcome,
          bfs_time_ns: round.bfs.time_ns,
          dp_time_ns: round.dp.time_ns,
          board_size: round.board.size,
          ladders: round.board.ladders,
          snakes: round.board.snakes,
        }),
      });

      const payload = await parseResponsePayload(response);
      if (!response.ok) {
        throw new Error(payload?.detail || `Could not save result (HTTP ${response.status}).`);
      }

      setResultMessage("WIN: correct answer saved to database.");
      setAnswerPopup({
        tone: "success",
        title: "Correct Answer",
        message: "Great job. Your answer is correct and has been saved.",
      });
      await loadDatabaseRows();
    } catch (error) {
      const text =
        error instanceof TypeError
          ? "Backend is offline. Could not save result."
          : error.message;
      setResultMessage(text);
    } finally {
      setLoading(false);
    }
  };

  const runBenchmark = async () => {
    setLoading(true);
    setBenchmarkRequested(true);
    setResultMessage("");

    try {
      const response = await fetch(`/api/benchmark?rounds=20&board_size=${Number(boardSize)}`);
      const payload = await parseResponsePayload(response);

      if (!response.ok) {
        throw new Error(payload?.detail || `Could not run benchmark (HTTP ${response.status}).`);
      }

      setBenchmark(payload);
      setResultMessage("Benchmark complete.");
    } catch (error) {
      const text =
        error instanceof TypeError
          ? "Connection failed: backend is unreachable for benchmark."
          : error.message;
      setResultMessage(text);
      setBenchmark(null);
    } finally {
      setLoading(false);
    }
  };

  const loadDatabaseRows = async () => {
    setLoading(true);
    setDbRequested(true);
    setDbMessage("Loading database output...");

    try {
      const response = await fetch("/api/database");
      const payload = await parseResponsePayload(response);
      if (!response.ok) {
        throw new Error(payload?.detail || `Could not load database snapshot (HTTP ${response.status}).`);
      }
      const snapshot = normalizeDatabaseSnapshot(payload);
      setDbSnapshot(snapshot);
      const totalRows =
        snapshot.players.length +
        snapshot.games.length +
        snapshot.game_jumps.length +
        snapshot.algorithm_runs.length;

      setDbMessage(`Loaded ${totalRows} rows from database.`);
      if (
        !snapshot.players.length &&
        !snapshot.games.length &&
        !snapshot.game_jumps.length &&
        !snapshot.algorithm_runs.length
      ) {
        setResultMessage("No saved rows yet.");
        setDbMessage("Database is reachable but no rows exist yet.");
      }
    } catch (error) {
      const text =
        error instanceof TypeError
          ? "Backend is offline. Could not load database output."
          : error.message;
      setResultMessage(text);
      setDbMessage(text);
      setDbSnapshot({ players: [], games: [], game_jumps: [], algorithm_runs: [] });
    } finally {
      setLoading(false);
    }
  };

  const openDatabasePage = async () => {
    if (window.location.hash !== "#database") {
      window.location.hash = "database";
    }
    setView("database");
    await loadDatabaseRows();
  };

  const backToGame = () => {
    window.location.hash = "";
    setView("game");
  };

  const exitSession = () => {
    setRound(null);
    setSelected(null);
    setBenchmark(null);
    setDbSnapshot({ players: [], games: [], game_jumps: [], algorithm_runs: [] });
    setBenchmarkRequested(false);
    setDbRequested(false);
    setDbMessage("");
    setResultMessage("Session ended. You can start again any time.");
  };

  if (view === "database") {
    return (
      <DatabasePage
        dbSnapshot={dbSnapshot}
        dbRequested={dbRequested}
        dbMessage={dbMessage}
        loading={loading}
        onReload={loadDatabaseRows}
        onBack={backToGame}
      />
    );
  }

  return (
    <div className="page">
      <header className="hero card">
        <h1>Snake and Ladder</h1>
        <p>
          Solve minimum throws, compare BFS vs DP timing, and benchmark 20 rounds on generated boards.
        </p>
        <div className="chips">
          <span>Board range: 6-12</span>
          <span>Benchmark: 20 rounds</span>
          <span>Storage: SQLite (correct answers only)</span>
        </div>
      </header>

      <section className="card setup-panel">
        <h2>Start Game</h2>
        <label htmlFor="playerName">Player name</label>
        <input
          id="playerName"
          type="text"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
          placeholder="Enter your name"
          maxLength={50}
        />

        <label htmlFor="boardSize">Board size (6 to 12)</label>
        <input
          id="boardSize"
          type="number"
          min={6}
          max={12}
          value={boardSize}
          onChange={(e) => setBoardSize(Number(e.target.value))}
        />

        <div className="actions">
          <button type="button" onClick={startRound} disabled={loading}>Start Round</button>
          <button type="button" className="ghost" onClick={openDatabasePage} disabled={loading}>Load DB Output</button>
        </div>
        {dbMessage ? <p className="status">{dbMessage}</p> : null}
      </section>

      <section className="info-grid">
        <article className="card info-card">
          <h3>Play Round</h3>
          <p>Start a random board and answer the minimum throws question.</p>
        </article>
        <article className="card info-card">
          <h3>20 Round Benchmark</h3>
          <p>Measure BFS and DP timing across generated rounds.</p>
        </article>
        <article className="card info-card">
          <h3>Database Output</h3>
          <p>Open the full normalized database on a separate page.</p>
        </article>
      </section>

      <section className="card round-panel">
        <h2>Current Round</h2>
        {round ? (
          <>
            <div className="metrics">
              <article className="metric bfs-metric">
                <h3>BFS</h3>
                <p>Throws: {round.bfs.minimum_throws}</p>
                <p>Time: {nsToMs(round.bfs.time_ns)} ms</p>
              </article>
              <article className="metric dp-metric">
                <h3>DP</h3>
                <p>Throws: {round.dp.minimum_throws}</p>
                <p>Time: {nsToMs(round.dp.time_ns)} ms</p>
              </article>
              <article className="metric board-metric">
                <h3>Board</h3>
                <p>Size: {round.board.size} x {round.board.size}</p>
                <p>Goal: {round.board.goal}</p>
              </article>
            </div>

            <BoardGrid board={round.board} />

            <div className="legend" aria-label="Board legend">
              <span><strong>Start</strong> cell 1</span>
              <span><strong>Goal</strong> cell N^2</span>
              <span><strong>🪜</strong> ladders</span>
              <span><strong>🐍</strong> snakes</span>
            </div>

            <div className="options" role="radiogroup" aria-label="Answer options">
              {round.options.map((option) => (
                <label key={option} className={selected === option ? "option active" : "option"}>
                  <input
                    type="radio"
                    name="answer"
                    checked={selected === option}
                    onChange={() => setSelected(option)}
                  />
                  {option} throws
                </label>
              ))}
            </div>

            <button onClick={submitAnswer} disabled={loading}>Submit Answer</button>
          </>
        ) : (
          <p className="empty">No round yet. Start a round to view metrics and board.</p>
        )}
      </section>

      <section className="card benchmark-panel">
        <h2>Benchmark</h2>
        {benchmark && benchmark.samples?.length ? (
          <>
            <div className="benchmark-summary">
              <p>Average BFS: {avg.bfs.toFixed(3)} ms</p>
              <p>Average DP: {avg.dp.toFixed(3)} ms</p>
            </div>
            <div className="bars">
              {benchmark.samples.map((sample) => (
                <div key={sample.round_number} className="bar-row">
                  <span className="round-tag">R{sample.round_number}</span>
                  <div className="bar-track">
                    <div
                      className="bar bfs"
                      style={{ width: `${Math.max((sample.bfs_ms / avg.maxMs) * 100, 2)}%` }}
                      title={`BFS ${sample.bfs_ms} ms`}
                    />
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar dp"
                      style={{ width: `${Math.max((sample.dp_ms / avg.maxMs) * 100, 2)}%` }}
                      title={`DP ${sample.dp_ms} ms`}
                    />
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : benchmarkRequested ? (
          <p className="empty">No benchmark yet.</p>
        ) : (
          <p className="empty">Run benchmark to see timing bars.</p>
        )}
      </section>

      <footer className="card footer-actions">
        <button onClick={runBenchmark} disabled={loading}>Run 20 Round Benchmark</button>
        <button className="ghost" onClick={exitSession} disabled={loading}>Exit</button>
        <p className="status" aria-live="polite">{loading ? "Working..." : resultMessage}</p>
      </footer>

      {answerPopup ? (
        <div className="popup-backdrop" role="presentation" onClick={() => setAnswerPopup(null)}>
          <div
            className={`popup-card ${answerPopup.tone === "success" ? "popup-success" : "popup-error"}`}
            role="dialog"
            aria-modal="true"
            aria-label={answerPopup.title}
            onClick={(e) => e.stopPropagation()}
          >
            <h3>{answerPopup.title}</h3>
            <p>{answerPopup.message}</p>
            <div className="actions">
              <button type="button" onClick={() => setAnswerPopup(null)}>OK</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default App;
