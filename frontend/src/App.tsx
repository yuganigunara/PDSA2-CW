import { useEffect, useRef, useState } from 'react';
import Board from './components/Board';
import SetupPanel from './components/SetupPanel';
import StatusPanel from './components/StatusPanel';
import {
    getPossibleMoves,
    positionKey,
    positionLabel,
    solveBacktracking,
    solveWarnsdorff,
    validatePath,
    type Position,
    type SolverMode,
    type WinnerRecord,
} from './knightTour';
import { APIService, type ScoreRecordResponse, type WinnerRecordResponse } from './api';
import knightIcon from './assets/knight-icon.svg';

type PlayMode = 'manual' | 'solver';
type BoardSize = 8 | 16;
type GameScreen = 'menu' | 'game';
type RoundResult = 'win' | 'lose' | 'draw' | null;

interface RoundScoreView {
    player: string;
    size: number;
    start: string;
    score: number;
    result: 'win' | 'lose' | 'draw';
    timestamp: string;
}

const WINNER_STORAGE_KEY = 'knights-tour-react-winners';
const DEFAULT_SPEED = 40;
const DEFAULT_NODE_LIMIT = 3_500_000;
const MAX_WINNERS = 6;

const GUIDE_STEPS = [
    {
        title: 'Pick a start square',
        text: 'Use the fields or click any square on the board to begin immediately.',
    },
    {
        title: 'Choose how to play',
        text: 'Manual mode lets you click the next legal move. Auto solve animates a full route.',
    },
    {
        title: 'Follow the route',
        text: 'Move numbers and highlights show exactly where the knight has been and where it can go next.',
    },
] as const;

function formatTimestamp(value: string): string {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        return value;
    }

    return parsed.toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

function readStoredWinners(): WinnerRecord[] {
    if (typeof window === 'undefined') {
        return [];
    }

    try {
        const raw = window.localStorage.getItem(WINNER_STORAGE_KEY);
        if (!raw) {
            return [];
        }

        const parsed = JSON.parse(raw) as unknown;
        if (!Array.isArray(parsed)) {
            return [];
        }

        return parsed.filter((item): item is WinnerRecord => {
            return Boolean(
                item
                && typeof item === 'object'
                && typeof (item as WinnerRecord).player === 'string'
                && typeof (item as WinnerRecord).size === 'number'
                && typeof (item as WinnerRecord).start === 'string'
                && typeof (item as WinnerRecord).pathLength === 'number'
                && typeof (item as WinnerRecord).timestamp === 'string'
                && Array.isArray((item as WinnerRecord).sequence),
            );
        });
    } catch {
        return [];
    }
}

function saveStoredWinners(winners: WinnerRecord[]): void {
    if (typeof window === 'undefined') {
        return;
    }

    window.localStorage.setItem(WINNER_STORAGE_KEY, JSON.stringify(winners.slice(0, MAX_WINNERS)));
}

function parseBoardIndex(value: string): number {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 1;
}

function createStartPosition(size: BoardSize, row: number, col: number): Position {
    return {
        row: Math.max(0, Math.min(size - 1, row - 1)),
        col: Math.max(0, Math.min(size - 1, col - 1)),
    };
}

function randomStartPosition(size: BoardSize): Position {
    return {
        row: Math.floor(Math.random() * size),
        col: Math.floor(Math.random() * size),
    };
}

function App() {
    const [screen, setScreen] = useState<GameScreen>('menu');
    const [boardSize, setBoardSize] = useState<BoardSize>(8);
    const [mode, setMode] = useState<PlayMode>('manual');
    const [solver, setSolver] = useState<SolverMode>('warnsdorff');
    const [startRow, setStartRow] = useState('1');
    const [startCol, setStartCol] = useState('1');
    const [playerName, setPlayerName] = useState('');
    const [nodeLimit, setNodeLimit] = useState(String(DEFAULT_NODE_LIMIT));
    const [speed, setSpeed] = useState(DEFAULT_SPEED);
    const [manualPath, setManualPath] = useState<Position[]>([]);
    const [solverPath, setSolverPath] = useState<Position[]>([]);
    const [animationIndex, setAnimationIndex] = useState(0);
    const [isAnimating, setIsAnimating] = useState(false);
    const [isSolving, setIsSolving] = useState(false);
    const [roundResult, setRoundResult] = useState<RoundResult>(null);
    const [playerNameError, setPlayerNameError] = useState('');
    const [showLeaderboard, setShowLeaderboard] = useState(false);
    const [leaderboardSort, setLeaderboardSort] = useState<'latest' | 'score'>('latest');
    const [showBackConfirm, setShowBackConfirm] = useState(false);
    const [isLoadingLeaderboard, setIsLoadingLeaderboard] = useState(false);
    const [leaderboardError, setLeaderboardError] = useState('');
    const [recentScores, setRecentScores] = useState<RoundScoreView[]>([]);
    const [status, setStatus] = useState('Pick a start square, then press Start Tour or run the auto solver.');
    const [recentWinners, setRecentWinners] = useState<WinnerRecord[]>(() => readStoredWinners());
    const animationRef = useRef<number | null>(null);

    const startPosition = createStartPosition(boardSize, parseBoardIndex(startRow), parseBoardIndex(startCol));
    const activePath = mode === 'solver' ? solverPath.slice(0, Math.max(1, animationIndex + 1)) : manualPath;
    const visited = new Set(activePath.map(positionKey));
    const currentPosition = activePath.length > 0 ? activePath[activePath.length - 1] : startPosition;
    const legalMoves = activePath.length > 0
        ? getPossibleMoves(boardSize, currentPosition.row, currentPosition.col, visited)
        : [];
    const currentCoverage = activePath.length > 0 ? activePath.length / (boardSize * boardSize) : 0;
    const isComplete = activePath.length === boardSize * boardSize;
    const trimmedPlayerName = playerName.trim();
    const hasUnsavedRoundProgress = activePath.length > 1 && !isComplete && roundResult === null;

    const sortedScores = [...recentScores].sort((left, right) => {
        if (leaderboardSort === 'score') {
            if (right.score !== left.score) {
                return right.score - left.score;
            }
        }
        return new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime();
    });

    useEffect(() => {
        if (boardSize === 16 && solver === 'backtracking') {
            setSolver('warnsdorff');
            setStatus('Warnsdorff is a better fit for 16x16, so the app switched automatically.');
        }
    }, [boardSize, solver]);

    useEffect(() => {
        if (!isAnimating) {
            return;
        }

        if (animationIndex >= solverPath.length - 1) {
            setIsAnimating(false);
            return;
        }

        animationRef.current = window.setTimeout(() => {
            setAnimationIndex((value: number) => value + 1);
        }, Math.max(45, 240 - speed * 3));

        return () => {
            if (animationRef.current !== null) {
                window.clearTimeout(animationRef.current);
            }
        };
    }, [animationIndex, isAnimating, solverPath.length, speed]);

    useEffect(() => {
        saveStoredWinners(recentWinners);
    }, [recentWinners]);

    useEffect(() => {
        void loadWinnersFromDb();
    }, []);

    useEffect(() => {
        if (mode !== 'manual' || roundResult !== null) {
            return;
        }

        if (manualPath.length > 0 && !isComplete && legalMoves.length === 0) {
            setRoundResult('lose');
            setStatus(`No legal moves left from ${positionLabel(currentPosition)}. Round result: Lose.`);
            saveRoundScore('lose', manualPath.length, startPosition);
        }
    }, [mode, roundResult, manualPath.length, isComplete, legalMoves.length, currentPosition]);

    async function loadWinnersFromDb() {
        setIsLoadingLeaderboard(true);
        setLeaderboardError('');
        try {
            const winners = await APIService.getWinners();
            const normalized = winners
                .filter((item: WinnerRecordResponse) => typeof item.player === 'string' && typeof item.pathLength === 'number')
                .slice(0, MAX_WINNERS);
            setRecentWinners(normalized);
        } catch {
            setLeaderboardError('Could not load leaderboard from database. Showing local history.');
        } finally {
            setIsLoadingLeaderboard(false);
        }
    }

    async function loadScoresFromDb() {
        setIsLoadingLeaderboard(true);
        setLeaderboardError('');
        try {
            const scores = await APIService.getScores();
            const normalized = scores
                .filter((item: ScoreRecordResponse) => typeof item.player === 'string' && typeof item.score === 'number')
                .slice(0, 30)
                .map((item: ScoreRecordResponse) => ({
                    player: item.player,
                    size: item.size,
                    start: item.start,
                    score: item.score,
                    result: item.result,
                    timestamp: item.timestamp,
                }));
            setRecentScores(normalized);
        } catch {
            setLeaderboardError('Could not load scores from database right now.');
        } finally {
            setIsLoadingLeaderboard(false);
        }
    }

    function saveRoundScore(result: 'win' | 'lose' | 'draw', score: number, start: Position) {
        void APIService.saveScore({
            player: playerName.trim() || 'Player',
            size: boardSize,
            start: positionLabel(start),
            score,
            result,
        }).then(() => {
            void loadScoresFromDb();
        }).catch(() => {
            // Best effort only.
        });
    }

    function recordWinner(path: Position[], start: Position, source: 'manual' | SolverMode) {
        const report = validatePath(boardSize, path, start);
        if (!report.valid) {
            return;
        }

        const winner: WinnerRecord = {
            player: playerName.trim() || 'Player',
            size: boardSize,
            start: positionLabel(start),
            pathLength: path.length,
            timestamp: new Date().toISOString(),
            sequence: path.map((step) => positionLabel(step)),
        };

        setRecentWinners((current: WinnerRecord[]) => [winner, ...current].slice(0, MAX_WINNERS));

        void APIService.saveWinner({
            player: winner.player,
            size: winner.size,
            path: path.map((step) => [step.row, step.col]),
            coverage: report.coverage,
            moves: path.length,
            solver: source,
        }).then(() => {
            void loadWinnersFromDb();
        }).catch(() => {
            // Keep gameplay smooth even if backend is temporarily unavailable.
        });
    }

    function resetTour(nextStatus: string) {
        setManualPath([]);
        setSolverPath([]);
        setAnimationIndex(0);
        setIsAnimating(false);
        setIsSolving(false);
        setRoundResult(null);
        setStatus(nextStatus);
    }

    function beginManualTour(roundStart: Position) {
        setMode('manual');
        setRoundResult(null);
        setStartRow(String(roundStart.row + 1));
        setStartCol(String(roundStart.col + 1));
        setManualPath([roundStart]);
        setSolverPath([]);
        setAnimationIndex(0);
        setIsAnimating(false);
        setStatus(`Manual tour started from ${positionLabel(roundStart)}. Click a highlighted square to continue.`);
    }

    function generateSolverTour(roundStart: Position) {
        setMode('solver');
        setRoundResult(null);
        setStartRow(String(roundStart.row + 1));
        setStartCol(String(roundStart.col + 1));
        setIsSolving(true);
        const limit = Number.parseInt(nodeLimit, 10);
        const safeLimit = Number.isFinite(limit) && limit > 0 ? limit : DEFAULT_NODE_LIMIT;

        // Try to use backend API first
        const tryBackendSolver = async () => {
            try {
                setStatus('Connecting to solver engine...');

                const response = await APIService.solve({
                    size: boardSize,
                    solver: solver,
                    startRow: roundStart.row,
                    startCol: roundStart.col,
                    nodeLimit: safeLimit,
                });

                if (!response.valid) {
                    setSolverPath([]);
                    setAnimationIndex(0);
                    setIsAnimating(false);
                    setRoundResult('draw');
                    setStatus('No full tour was found for this random start. Round result: Draw.');
                    saveRoundScore('draw', 0, roundStart);
                    setIsSolving(false);
                    return;
                }

                const path: Position[] = response.path.map(([row, col]) => ({ row, col }));
                setSolverPath(path);
                setAnimationIndex(0);
                setIsAnimating(true);
                setRoundResult('win');
                setStatus(`✓ Backend solver found a ${solver === 'warnsdorff' ? 'Warnsdorff' : 'backtracking'} route (${(response.coverage * 100).toFixed(1)}% coverage).`);

                // Save winner using backend
                recordWinner(path, roundStart, solver);
                saveRoundScore('win', path.length, roundStart);

                setIsSolving(false);
            } catch (error) {
                // Fall back to browser solver
                console.log('Backend unavailable, using browser solver:', error);
                useBrowserSolver();
            }
        };

        const useBrowserSolver = () => {
            setStatus('Using browser solver...');
            const result = solver === 'warnsdorff'
                ? solveWarnsdorff(boardSize, roundStart)
                : solveBacktracking(boardSize, roundStart, safeLimit);

            if (!result) {
                setSolverPath([]);
                setAnimationIndex(0);
                setIsAnimating(false);
                setRoundResult('draw');
                setStatus('No full tour was found for this random start. Round result: Draw.');
                saveRoundScore('draw', 0, roundStart);
                setIsSolving(false);
                return;
            }

            setSolverPath(result);
            setAnimationIndex(0);
            setIsAnimating(true);
            setRoundResult('win');
            setStatus(`Auto tour ready. Knight route is starting with ${solver === 'warnsdorff' ? 'Warnsdorff' : 'backtracking'}.`);
            recordWinner(result, roundStart, solver);
            saveRoundScore('win', result.length, roundStart);
            setIsSolving(false);
        };

        tryBackendSolver();
    }

    function handleCellClick(cell: Position) {
        if (mode !== 'manual') {
            return;
        }

        if (manualPath.length === 0) {
            setStartRow(String(cell.row + 1));
            setStartCol(String(cell.col + 1));
            setManualPath([cell]);
            setStatus(`Start set to ${positionLabel(cell)}. Choose the next legal move.`);
            return;
        }

        const isLegalMove = legalMoves.some((move) => move.row === cell.row && move.col === cell.col);
        if (!isLegalMove) {
            setStatus(`Illegal move to ${positionLabel(cell)}. Pick one of the highlighted legal moves.`);
            return;
        }

        const nextPath = [...manualPath, cell];
        setManualPath(nextPath);

        const report = validatePath(boardSize, nextPath, startPosition);
        if (report.valid) {
            setRoundResult('win');
            setStatus(`Tour completed in ${nextPath.length} moves. Nice work.`);
            recordWinner(nextPath, startPosition, 'manual');
            saveRoundScore('win', nextPath.length, startPosition);
            return;
        }

        setStatus(`Moved to ${positionLabel(cell)}. ${report.reason}`);
    }

    function undoMove() {
        if (mode !== 'manual' || manualPath.length <= 1) {
            return;
        }

        const nextPath = manualPath.slice(0, -1);
        setManualPath(nextPath);
        setStatus(`Undid the last move. Current square: ${positionLabel(nextPath[nextPath.length - 1])}.`);
    }

    function clearBoard() {
        if (activePath.length > 1 && !isComplete) {
            setRoundResult('draw');
            saveRoundScore('draw', activePath.length, startPosition);
            resetTour('Round ended before completion. Round result: Draw.');
            return;
        }

        resetTour('Board cleared. Choose a new start square to begin again.');
    }

    function startNewRound() {
        const randomStart = randomStartPosition(boardSize);
        if (mode === 'solver') {
            generateSolverTour(randomStart);
            return;
        }

        beginManualTour(randomStart);
    }

    function enterGameFromMenu() {
        if (!trimmedPlayerName) {
            setPlayerNameError('Please enter your name before starting.');
            return;
        }

        setPlayerNameError('');
        setScreen('game');
        setMode('manual');
        beginManualTour(randomStartPosition(boardSize));
    }

    function backToMenu() {
        if (hasUnsavedRoundProgress) {
            setShowBackConfirm(true);
            return;
        }

        setScreen('menu');
        resetTour('Returned to menu. You can start a new round anytime.');
    }

    function confirmBackToMenu() {
        if (hasUnsavedRoundProgress) {
            saveRoundScore('draw', activePath.length, startPosition);
        }
        setShowBackConfirm(false);
        setScreen('menu');
        resetTour('Returned to menu. You can start a new round anytime.');
    }

    function cancelBackToMenu() {
        setShowBackConfirm(false);
    }

    function toggleLeaderboard() {
        setShowLeaderboard((value) => {
            const next = !value;
            if (next) {
                void loadScoresFromDb();
            }
            return next;
        });
    }

    function backToGameHubDashboard() {
        if (window.history.length > 1) {
            window.history.back();
            return;
        }

        window.location.assign('http://localhost:5180/');
    }

    if (screen === 'menu') {
        return (
            <div className="app-shell">
                <div className="ambient ambient-left" />
                <div className="ambient ambient-right" />
                <main className="page-shell">
                    <section className="card menu-card">
                        <img className="hero-knight-icon" src={knightIcon} alt="Knight icon" />
                        <p className="eyebrow">Game Menu</p>
                        <h1>Knight's Tour Problem</h1>
                        <p className="hero-copy">
                            Start with a random knight position and cover every square exactly once. Select board size and enter the challenge.
                        </p>
                        <div className="menu-controls">
                            <label>
                                Player name
                                <input
                                    value={playerName}
                                    onChange={(event) => {
                                        setPlayerName(event.target.value);
                                        if (event.target.value.trim()) {
                                            setPlayerNameError('');
                                        }
                                    }}
                                    placeholder="Your name"
                                    aria-invalid={Boolean(playerNameError)}
                                    className={playerNameError ? 'input-invalid' : ''}
                                />
                            </label>
                            {playerNameError ? <p className="validation-message">{playerNameError}</p> : null}
                            <label>
                                Board size
                                <select value={boardSize} onChange={(event) => setBoardSize(Number(event.target.value) as BoardSize)}>
                                    <option value={8}>8 x 8</option>
                                    <option value={16}>16 x 16</option>
                                </select>
                            </label>
                            <div className="menu-actions">
                                <button className="primary-button" type="button" onClick={enterGameFromMenu} disabled={!trimmedPlayerName}>
                                    Start Playing
                                </button>
                                <button className="secondary-button" type="button" onClick={toggleLeaderboard}>
                                    {showLeaderboard ? 'Hide Player Scores' : 'Show Player Scores'}
                                </button>
                                <button className="secondary-button" type="button" onClick={backToGameHubDashboard}>
                                    Back to Game Hub
                                </button>
                            </div>
                        </div>

                        {showLeaderboard ? (
                            <section className="menu-leaderboard">
                                <div className="menu-leaderboard-head">
                                    <h2>Player Scores</h2>
                                    <div className="leaderboard-controls">
                                        <label className="leaderboard-sort" htmlFor="leaderboard-sort">
                                            Sort by
                                            <select
                                                id="leaderboard-sort"
                                                value={leaderboardSort}
                                                onChange={(event) => setLeaderboardSort(event.target.value as 'latest' | 'score')}
                                            >
                                                <option value="latest">Latest First</option>
                                                <option value="score">Highest Score</option>
                                            </select>
                                        </label>
                                        <button className="secondary-button leaderboard-refresh" type="button" onClick={() => void loadScoresFromDb()}>
                                            Refresh
                                        </button>
                                    </div>
                                </div>
                                {isLoadingLeaderboard ? <p className="muted">Loading...</p> : null}
                                {leaderboardError ? <p className="muted">{leaderboardError}</p> : null}
                                <div className="leaderboard-wrap">
                                    <table className="leaderboard-table">
                                        <thead>
                                            <tr>
                                                <th>Player</th>
                                                <th>Board</th>
                                                <th>Score</th>
                                                <th>Start</th>
                                                <th>Saved</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {sortedScores.length === 0 ? (
                                                <tr>
                                                    <td colSpan={5}>No scores in database yet.</td>
                                                </tr>
                                            ) : sortedScores.map((row) => (
                                                <tr key={`${row.timestamp}-${row.player}-${row.result}`}>
                                                    <td>{row.player}</td>
                                                    <td>{row.size}x{row.size}</td>
                                                    <td>{row.score} ({row.result})</td>
                                                    <td>{row.start}</td>
                                                    <td>{formatTimestamp(row.timestamp)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </section>
                        ) : null}
                    </section>
                </main>
            </div>
        );
    }

    return (
        <div className="app-shell">
            <div className="ambient ambient-left" />
            <div className="ambient ambient-right" />

            <main className="page-shell">
                <section className="hero card">
                    <div>
                        <img className="hero-knight-icon" src={knightIcon} alt="Knight icon" />
                        <p className="eyebrow">React Knight's Tour</p>
                        <h1>A calmer, clearer way to play the Knight's Tour.</h1>
                        <p className="hero-copy">
                            Start with one square, then either follow the legal moves yourself or let the solver animate a full tour.
                            The board stays front and center, and the advanced options stay out of your way.
                        </p>

                        <div className="hero-actions">
                            <button className="primary-button" type="button" onClick={startNewRound}>
                                {mode === 'manual' ? 'Start Tour' : 'Generate Auto Tour'}
                            </button>
                            <button className="secondary-button" type="button" onClick={clearBoard}>
                                Reset Board
                            </button>
                            <button className="secondary-button" type="button" onClick={backToMenu}>
                                Back to Menu
                            </button>
                        </div>
                    </div>

                    <div className="hero-guide">
                        {GUIDE_STEPS.map((step, index) => (
                            <article key={step.title} className="guide-step">
                                <span>{index + 1}</span>
                                <div>
                                    <strong>{step.title}</strong>
                                    <p>{step.text}</p>
                                </div>
                            </article>
                        ))}
                    </div>
                </section>

                <section className="workspace-grid">
                    <div className="main-column">
                        <SetupPanel
                            boardSize={boardSize}
                            solver={solver}
                            mode={mode}
                            isSolving={isSolving}
                            startRow={startRow}
                            startCol={startCol}
                            playerName={playerName}
                            nodeLimit={nodeLimit}
                            onBoardSizeChange={setBoardSize}
                            onSolverChange={setSolver}
                            onModeChange={setMode}
                            onStartRowChange={setStartRow}
                            onStartColChange={setStartCol}
                            onPlayerNameChange={setPlayerName}
                            onNodeLimitChange={setNodeLimit}
                            onStartNewRound={startNewRound}
                            onUndoMove={undoMove}
                            onClearBoard={clearBoard}
                        />

                        <section className="card board-card">
                            <div className="section-head board-head">
                                <div>
                                    <p className="card-kicker">Board</p>
                                    <h2>{mode === 'manual' ? 'Click the glowing squares' : 'Watch the route animate'}</h2>
                                    <p className="board-note">
                                        {mode === 'manual'
                                            ? 'If you have not started yet, click any square on the board to set the start instantly.'
                                            : 'The board is animated step by step so the whole tour is easy to follow.'}
                                    </p>
                                </div>

                                <div className="board-meta">
                                    <div>
                                        <span>Current square</span>
                                        <strong>{positionLabel(currentPosition)}</strong>
                                    </div>
                                    <div>
                                        <span>Coverage</span>
                                        <strong>{Math.round(currentCoverage * 100)}%</strong>
                                    </div>
                                    <label className="speed-control">
                                        Speed
                                        <input
                                            type="range"
                                            min="5"
                                            max="120"
                                            value={speed}
                                            onChange={(event) => setSpeed(Number(event.target.value))}
                                        />
                                    </label>
                                </div>
                            </div>

                            <Board
                                boardSize={boardSize}
                                mode={mode}
                                startPosition={startPosition}
                                activePath={activePath}
                                currentPosition={currentPosition}
                                legalMoves={legalMoves}
                                manualPathLength={manualPath.length}
                                onCellClick={handleCellClick}
                            />

                            <div className="legend">
                                <span><i className="legend-start" /> Start</span>
                                <span><i className="legend-current" /> Current</span>
                                <span><i className="legend-legal" /> Legal move</span>
                                <span><i className="legend-visited" /> Visited</span>
                            </div>
                        </section>
                    </div>

                    <StatusPanel
                        status={status}
                        roundResult={roundResult}
                        currentPosition={currentPosition}
                        currentCoverage={currentCoverage}
                        isComplete={isComplete}
                        legalMovesLength={legalMoves.length}
                        startPosition={startPosition}
                        activePath={activePath}
                        recentWinners={recentWinners}
                    />
                </section>
            </main>

            {showBackConfirm ? (
                <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="back-confirm-title">
                    <div className="modal-card">
                        <h2 id="back-confirm-title">Leave this round?</h2>
                        <p>You have unfinished moves. If you go back now, this round progress will be lost.</p>
                        <div className="modal-actions">
                            <button className="secondary-button" type="button" onClick={cancelBackToMenu}>
                                Stay Here
                            </button>
                            <button className="primary-button" type="button" onClick={confirmBackToMenu}>
                                Leave Round
                            </button>
                        </div>
                    </div>
                </div>
            ) : null}
        </div>
    );
}

export default App;
