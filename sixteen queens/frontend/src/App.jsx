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
const graphWidth = 980;
const graphHeight = 340;
const graphMargin = { top: 24, right: 24, bottom: 56, left: 76 };

function buildSeries(rounds, algorithm, field) {
  return rounds
    .map((round, index) => ({
      index: index + 1,
      round_no: round.round_no,
      value: Number(round?.[algorithm]?.[field] || 0),
    }))
    .filter((point) => point.value > 0);
}

function GraphCard({
  title,
  chip,
  legendLeft,
  legendRight,
  yLabel,
  series,
  valueFormatter,
  valueScale = 1,
  fixedYDomainMin,
  fixedYDomainMax,
  fixedYTickStep,
  fixedYTickCount,
  domainPadding = 0,
  xLabelEvery = 1,
  hoverPointLabels = false,
}) {
  const flatValues = series.flatMap((item) => item.points.map((point) => point.value));
  const maxValue = Math.max(1, ...flatValues);
  const minValue = Math.min(...flatValues, maxValue);
  const yDomainMin = typeof fixedYDomainMin === "number" ? fixedYDomainMin : Math.max(0, minValue - domainPadding);
  const yDomainMax = typeof fixedYDomainMax === "number" ? fixedYDomainMax : maxValue + domainPadding;
  const innerWidth = graphWidth - graphMargin.left - graphMargin.right;
  const innerHeight = graphHeight - graphMargin.top - graphMargin.bottom;
  const xCount = Math.max(1, series[0]?.points.length || 0);
  const yDomainSpan = Math.max(1, yDomainMax - yDomainMin);

  const chartSeries = series.map((item, seriesIndex) => {
    const points = item.points.map((point) => {
      const x = graphMargin.left + (xCount === 1 ? innerWidth / 2 : ((point.index - 1) / (xCount - 1)) * innerWidth);
      const y = graphMargin.top + innerHeight - ((point.value - yDomainMin) / yDomainSpan) * innerHeight;
      return { ...point, x, y };
    });
    return { ...item, points, colorIndex: seriesIndex };
  });

  const yTickValues = fixedYTickStep
    ? Array.from({ length: Math.floor((yDomainMax - yDomainMin) / fixedYTickStep) + 1 }, (_, index) => yDomainMin + index * fixedYTickStep)
    : Array.from({ length: (fixedYTickCount || 5) + 1 }, (_, index) => yDomainMin + (yDomainSpan / (fixedYTickCount || 5)) * index);
  const xTickValues = Array.from({ length: xCount }, (_, index) => index + 1).filter(
    (roundNo) => roundNo === 1 || roundNo === xCount || (roundNo - 1) % xLabelEvery === 0
  );

  return (
    <section className="panel chart-panel">
      <div className="panel-head">
        <h2>{title}</h2>
        <span className="chip">{chip}</span>
      </div>

      {!series.some((item) => item.points.length) && (
        <div className="banner banner-ok">No benchmark data yet. Run 20 tests to populate this graph.</div>
      )}

      <div className="graph-layout">
        <div className="graph-wrap">
          <svg viewBox={`0 0 ${graphWidth} ${graphHeight}`} role="img" aria-label={title} className="line-graph">
            {yTickValues.map((value) => {
              const y = graphMargin.top + innerHeight - ((value - yDomainMin) / yDomainSpan) * innerHeight;
              return (
                <g key={`tick-${value}`}>
                  <line x1={graphMargin.left} y1={y} x2={graphWidth - graphMargin.right} y2={y} className="graph-grid" />
                  <line x1={graphMargin.left - 6} y1={y} x2={graphMargin.left} y2={y} className="graph-axis" />
                  <text x={graphMargin.left - 10} y={y + 4} className="graph-y-label" textAnchor="end">
                    {valueFormatter(value / valueScale)}
                  </text>
                </g>
              );
            })}

            <line x1={graphMargin.left} y1={graphMargin.top + innerHeight} x2={graphWidth - graphMargin.right} y2={graphMargin.top + innerHeight} className="graph-axis" />
            <line x1={graphMargin.left} y1={graphMargin.top} x2={graphMargin.left} y2={graphMargin.top + innerHeight} className="graph-axis" />

            {chartSeries.map((item) => {
              const linePoints = item.points.map((point) => `${point.x},${point.y}`).join(" ");
              return (
                <g key={item.label} className={`graph-series series-${item.colorIndex}`}>
                  <polyline points={linePoints} className="graph-line" />
                  {item.points.map((point) => (
                    <g key={`${item.label}-${point.round_no}`} className="graph-point-group">
                      <circle cx={point.x} cy={point.y} r="5" className="graph-dot" />
                      {hoverPointLabels && (
                        <text
                          x={point.x + (item.colorIndex === 0 ? -6 : 6)}
                          y={point.y - 8}
                          className={`graph-point-label ${item.colorIndex === 0 ? "point-left" : "point-right"}`}
                          textAnchor={item.colorIndex === 0 ? "end" : "start"}
                        >
                          {valueFormatter(point.value / valueScale)}
                        </text>
                      )}
                    </g>
                  ))}
                </g>
              );
            })}

            {xTickValues.map((roundNo) => {
              const x = graphMargin.left + (xCount === 1 ? innerWidth / 2 : ((roundNo - 1) / (xCount - 1)) * innerWidth);
              return (
                <text key={`round-${roundNo}`} x={x} y={graphMargin.top + innerHeight + 18} className="graph-round" textAnchor="middle">
                  {roundNo}
                </text>
              );
            })}

            <text x={graphMargin.left + innerWidth / 2} y={graphHeight - 8} className="graph-x-title" textAnchor="middle">
              Game Round (1-20)
            </text>
            <text x={18} y={graphMargin.top + innerHeight / 2} className="graph-y-title" textAnchor="middle" transform={`rotate(-90 18 ${graphMargin.top + innerHeight / 2})`}>
              {yLabel}
            </text>
          </svg>
        </div>

        <aside className="graph-legend-box">
          <div className="legend-item"><span className="legend-dot series-0" />{legendLeft}</div>
          <div className="legend-item"><span className="legend-dot series-1" />{legendRight}</div>
        </aside>
      </div>
    </section>
  );
}

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
    return [...map.values()].slice(-20);
  }, [state]);

  const timeSeries = useMemo(
    () => [
      { label: "Sequential", points: buildSeries(rounds, "sequential", "time_ns") },
      { label: "Threaded", points: buildSeries(rounds, "threaded", "time_ns") },
    ],
    [rounds]
  );

  const spaceSeries = useMemo(
    () => [
      { label: "Sequential", points: buildSeries(rounds, "sequential", "peak_bytes") },
      { label: "Threaded", points: buildSeries(rounds, "threaded", "peak_bytes") },
    ],
    [rounds]
  );

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

      <GraphCard
        title="Time Taken Chart"
        chip="Last 20 rounds from sqlite"
        legendLeft="Sequential"
        legendRight="Threaded"
        yLabel="time in milliseconds"
        series={timeSeries}
        valueFormatter={formatMs}
        valueScale={1}
        domainPadding={10 * 1e6}
        fixedYTickCount={9}
        xLabelEvery={1}
        hoverPointLabels={true}
      />

      <GraphCard
        title="Space Taken Chart"
        chip="Peak memory for last 20 rounds"
        legendLeft="Sequential"
        legendRight="Threaded"
        yLabel="peak memory in KB"
        series={spaceSeries}
        valueFormatter={formatKb}
        valueScale={1}
        domainPadding={0.2 * 1024}
        fixedYTickCount={9}
        hoverPointLabels={true}
      />

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
