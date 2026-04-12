import { getPossibleMoves, positionKey, type Position } from '../knightTour';
import knightIcon from '../assets/knight-icon.svg';

type PlayMode = 'manual' | 'solver';

interface BoardProps {
    boardSize: 8 | 16;
    mode: PlayMode;
    startPosition: Position;
    activePath: Position[];
    currentPosition: Position;
    legalMoves: Position[];
    manualPathLength: number;
    onCellClick: (cell: Position) => void;
}

function Board({
    boardSize,
    mode,
    startPosition,
    activePath,
    currentPosition,
    legalMoves,
    manualPathLength,
    onCellClick,
}: BoardProps) {
    const visited = new Set(activePath.map(positionKey));
    const isManualReady = mode === 'manual' && manualPathLength > 0;

    function renderCell(row: number, col: number) {
        const cell: Position = { row, col };
        const key = positionKey(cell);
        const isDark = (row + col) % 2 === 1;
        const moveIndex = activePath.findIndex((step: Position) => step.row === row && step.col === col);
        const isStart = row === startPosition.row && col === startPosition.col;
        const isCurrent = currentPosition.row === row && currentPosition.col === col && activePath.length > 0;
        const isVisited = visited.has(key);
        const isLegal = legalMoves.some((move) => move.row === row && move.col === col);
        const isPreviewStart = mode === 'manual' && manualPathLength === 0 && isStart;
        const classes = [
            'cell',
            isDark ? 'cell-dark' : 'cell-light',
            isVisited ? 'cell-visited' : '',
            isCurrent ? 'cell-current' : '',
            isStart ? 'cell-start' : '',
            isPreviewStart ? 'cell-start-preview' : '',
            isLegal ? 'cell-legal' : '',
        ]
            .filter(Boolean)
            .join(' ');

        return (
            <button
                key={key}
                className={classes}
                type="button"
                onClick={() => onCellClick(cell)}
                aria-label={`Row ${row + 1}, column ${col + 1}`}
            >
                <span className="cell-label">{moveIndex >= 0 ? moveIndex + 1 : row + 1}</span>
                {isCurrent && <img className="cell-knight" src={knightIcon} alt="" aria-hidden="true" />}
                {isPreviewStart && <span className="cell-tag">Start here</span>}
                {isStart && !isPreviewStart && <span className="cell-tag">Start</span>}
                {isCurrent && <span className="cell-tag cell-tag-current">Knight</span>}
                {isLegal && isManualReady && <span className="cell-ring" />}
            </button>
        );
    }

    return (
        <div className="board-frame">
            <div className="board" style={{ gridTemplateColumns: `repeat(${boardSize}, minmax(0, 1fr))` }}>
                {Array.from({ length: boardSize }).flatMap((_, row) =>
                    Array.from({ length: boardSize }, (_, col) => renderCell(row, col)),
                )}
            </div>
        </div>
    );
}

export default Board;
