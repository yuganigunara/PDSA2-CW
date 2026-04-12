import type { SolverMode } from '../knightTour';

type PlayMode = 'manual' | 'solver';

interface SetupPanelProps {
    boardSize: 8 | 16;
    solver: SolverMode;
    mode: PlayMode;
    isSolving: boolean;
    startRow: string;
    startCol: string;
    playerName: string;
    nodeLimit: string;
    onBoardSizeChange: (value: 8 | 16) => void;
    onSolverChange: (value: SolverMode) => void;
    onModeChange: (value: PlayMode) => void;
    onStartRowChange: (value: string) => void;
    onStartColChange: (value: string) => void;
    onPlayerNameChange: (value: string) => void;
    onNodeLimitChange: (value: string) => void;
    onStartNewRound: () => void;
    onUndoMove: () => void;
    onClearBoard: () => void;
}

function SetupPanel({
    boardSize,
    solver,
    mode,
    isSolving,
    startRow,
    startCol,
    playerName,
    nodeLimit,
    onBoardSizeChange,
    onSolverChange,
    onModeChange,
    onStartRowChange,
    onStartColChange,
    onPlayerNameChange,
    onNodeLimitChange,
    onStartNewRound,
    onUndoMove,
    onClearBoard,
}: SetupPanelProps) {
    return (
        <section className="card setup-card" aria-busy={isSolving}>
            <div className="section-head">
                <div>
                    <p className="card-kicker">Play Settings</p>
                    <h2>Keep the setup simple</h2>
                    <p className="muted">Tip: Pick a start square, then press one button to play or auto-solve.</p>
                </div>

                <div className="mode-switch" role="tablist" aria-label="Play mode">
                    <button
                        className={mode === 'manual' ? 'mode-pill active' : 'mode-pill'}
                        type="button"
                        disabled={isSolving}
                        onClick={() => onModeChange('manual')}
                    >
                        Manual
                    </button>
                    <button
                        className={mode === 'solver' ? 'mode-pill active' : 'mode-pill'}
                        type="button"
                        disabled={isSolving}
                        onClick={() => onModeChange('solver')}
                    >
                        Auto Solve
                    </button>
                </div>
            </div>

            <div className="field-grid">
                <label>
                    Board size
                    <select disabled={isSolving} value={boardSize} onChange={(event) => onBoardSizeChange(Number(event.target.value) as 8 | 16)}>
                        <option value={8}>8 x 8</option>
                        <option value={16}>16 x 16</option>
                    </select>
                </label>

                <label>
                    Player name
                    <input
                        disabled={isSolving}
                        value={playerName}
                        onChange={(event) => onPlayerNameChange(event.target.value)}
                        placeholder="Your name"
                    />
                </label>

                <label>
                    Start row
                    <input
                        disabled={isSolving}
                        value={startRow}
                        onChange={(event) => onStartRowChange(event.target.value)}
                        inputMode="numeric"
                        placeholder="1"
                    />
                </label>

                <label>
                    Start column
                    <input
                        disabled={isSolving}
                        value={startCol}
                        onChange={(event) => onStartColChange(event.target.value)}
                        inputMode="numeric"
                        placeholder="1"
                    />
                </label>

                <label>
                    Solver strategy
                    <select disabled={isSolving} value={solver} onChange={(event) => onSolverChange(event.target.value as SolverMode)}>
                        <option value="warnsdorff">Warnsdorff heuristic</option>
                        <option value="backtracking">Backtracking search</option>
                    </select>
                </label>

                <label>
                    Node limit
                    <input
                        disabled={isSolving}
                        value={nodeLimit}
                        onChange={(event) => onNodeLimitChange(event.target.value)}
                        inputMode="numeric"
                    />
                </label>
            </div>

            <div className="action-row">
                <button className="primary-button" type="button" disabled={isSolving} onClick={onStartNewRound}>
                    {isSolving ? 'Summoning Knight...' : mode === 'manual' ? 'Start Tour' : 'Run Solver'}
                </button>
                <button className="secondary-button" type="button" disabled={isSolving || mode !== 'manual'} onClick={onUndoMove}>Undo</button>
                <button className="secondary-button" type="button" disabled={isSolving} onClick={onClearBoard}>Reset</button>
            </div>
        </section>
    );
}

export default SetupPanel;
