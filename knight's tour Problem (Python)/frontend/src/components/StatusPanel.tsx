import { positionLabel, type Position, type WinnerRecord } from '../knightTour';

interface RoundScoreView {
    player: string;
    size: number;
    start: string;
    result: 'win' | 'lose' | 'draw';
    moves: number;
    timestamp: string;
}

interface StatusPanelProps {
    status: string;
    roundResult: 'win' | 'lose' | 'draw' | null;
    currentPosition: Position;
    currentCoverage: number;
    isComplete: boolean;
    legalMovesLength: number;
    startPosition: Position;
    activePath: Position[];
    recentWinners: WinnerRecord[];
    recentScores: RoundScoreView[];
}

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

function StatusPanel({
    status,
    roundResult,
    currentPosition,
    currentCoverage,
    isComplete,
    legalMovesLength,
    startPosition,
    activePath,
    recentWinners,
    recentScores,
}: StatusPanelProps) {
    const resultLabel = roundResult === 'win'
        ? 'Win'
        : roundResult === 'lose'
            ? 'Lose'
            : roundResult === 'draw'
                ? 'Draw'
                : 'In Progress';

    return (
        <aside className="side-column">
            <section className="card info-card status-card">
                <p className="card-kicker">Status</p>
                <h2>What to do next</h2>
                <p className={`result-pill ${roundResult ? `result-${roundResult}` : 'result-playing'}`}>{resultLabel}</p>
                <p className="status-text">{status}</p>

                <div className="progress-track" aria-hidden="true">
                    <div className="progress-fill" style={{ width: `${currentCoverage * 100}%` }} />
                </div>

                <div className="status-grid">
                    <div>
                        <span>Mode</span>
                        <strong>{activePath.length > 0 ? 'In progress' : 'Ready'}</strong>
                    </div>
                    <div>
                        <span>Legal moves</span>
                        <strong>{legalMovesLength}</strong>
                    </div>
                    <div>
                        <span>Complete</span>
                        <strong>{isComplete ? 'Yes' : 'No'}</strong>
                    </div>
                    <div>
                        <span>Start</span>
                        <strong>{positionLabel(startPosition)}</strong>
                    </div>
                </div>

                <div className="status-grid" style={{ marginTop: '12px' }}>
                    <div>
                        <span>Current square</span>
                        <strong>{positionLabel(currentPosition)}</strong>
                    </div>
                    <div>
                        <span>Coverage</span>
                        <strong>{Math.round(currentCoverage * 100)}%</strong>
                    </div>
                </div>
            </section>

            <section className="card info-card">
                <p className="card-kicker">Route</p>
                <h2>Recent moves</h2>
                <ol className="move-list">
                    {(activePath.length > 0 ? activePath : [startPosition]).slice(-10).map((step, index, array) => {
                        const absoluteIndex = activePath.length > 10 ? activePath.length - array.length + index + 1 : index + 1;
                        return (
                            <li key={`${step.row}-${step.col}-${absoluteIndex}`}>
                                <span>{absoluteIndex}</span>
                                <strong>{positionLabel(step)}</strong>
                            </li>
                        );
                    })}
                </ol>
            </section>

            <section className="card info-card winners-card">
                <p className="card-kicker">Saved</p>
                <h2>Recent results</h2>
                <div className="winner-list">
                    {recentScores.length === 0 ? (
                        <p className="muted">No saved results yet. Complete a round and it will appear here.</p>
                    ) : recentScores.slice().reverse().map((score, idx) => (
                        <article key={`${score.timestamp}-${score.player}-${idx}`} className={`winner-item result-${score.result}`}>
                            <div>
                                <strong>{score.player}</strong>
                                <span>{score.size} x {score.size} from {score.start}</span>
                            </div>
                            <div>
                                <strong>{score.moves} moves</strong>
                                <span>{score.result.charAt(0).toUpperCase() + score.result.slice(1)}</span>
                                <span>{formatTimestamp(score.timestamp)}</span>
                            </div>
                        </article>
                    ))}
                </div>
            </section>
        </aside>
    );
}

export default StatusPanel;
