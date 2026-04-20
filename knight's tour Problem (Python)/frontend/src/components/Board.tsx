
import { getPossibleMoves, positionKey, type Position } from '../knightTour';
import knightIcon from '../assets/knight-icon.svg';
import React, { useRef, useEffect, useMemo } from 'react';

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
    const boardRef = useRef<HTMLDivElement>(null);
    const lastMove = activePath.length > 1 ? activePath[activePath.length - 2] : null;
    const isComplete = activePath.length === boardSize * boardSize;
    // Memoized move index map for performance
    const moveIndexMap = useMemo(() => new Map(activePath.map((p, i) => [positionKey(p), i])), [activePath]);

    // Focus the current cell for accessibility
    useEffect(() => {
        if (boardRef.current) {
            const currentBtn = boardRef.current.querySelector('.cell-current');
            if (currentBtn) {
                (currentBtn as HTMLElement).focus();
            }
        }
    }, [currentPosition]);

    // Improved keyboard navigation for knight's 8 moves and spacebar
    useEffect(() => {
        function handleKeyDown(e: KeyboardEvent) {
            if (!isManualReady) return;
            const knightMoves = [
                { row: -2, col: -1 }, { row: -2, col: 1 },
                { row: -1, col: -2 }, { row: -1, col: 2 },
                { row: 1, col: -2 }, { row: 1, col: 2 },
                { row: 2, col: -1 }, { row: 2, col: 1 },
            ];
            const { row, col } = currentPosition;
            let next: Position | null = null;
            // Use number keys 1-8 for knight moves
            if (e.key >= '1' && e.key <= '8') {
                const idx = parseInt(e.key, 10) - 1;
                if (legalMoves[idx]) onCellClick(legalMoves[idx]);
                return;
            }
            // Spacebar: auto move to first legal move
            if (e.key === ' ') {
                if (legalMoves[0]) onCellClick(legalMoves[0]);
                return;
            }
            // Arrow keys: try all knight moves
            for (const move of knightMoves) {
                const candidate = { row: row + move.row, col: col + move.col };
                if (legalMoves.some((m) => m.row === candidate.row && m.col === candidate.col)) {
                    next = candidate;
                    break;
                }
            }
            if (next) onCellClick(next);
        }
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [currentPosition, legalMoves, isManualReady, onCellClick]);


    function renderCell(row: number, col: number) {
        const cell: Position = { row, col };
        const key = positionKey(cell);
        const isDark = (row + col) % 2 === 1;
        const moveIndex = moveIndexMap.get(key);
        const isStart = row === startPosition.row && col === startPosition.col;
        const isCurrent = currentPosition.row === row && currentPosition.col === col && activePath.length > 0;
        const isVisited = visited.has(key);
        const isLegal = legalMoves.some((move) => move.row === row && move.col === col);
        const isPreviewStart = mode === 'manual' && manualPathLength === 0 && isStart;
        const isLastMove = lastMove && lastMove.row === row && lastMove.col === col;
        const isDisabled = isManualReady && !isLegal && !isCurrent;
        const classes = [
            'cell',
            isDark ? 'cell-dark' : 'cell-light',
            isVisited ? 'cell-visited' : '',
            isCurrent ? 'cell-current' : '',
            isStart ? 'cell-start' : '',
            isPreviewStart ? 'cell-start-preview' : '',
            isLegal ? 'cell-legal' : '',
            isLastMove ? 'cell-last-move' : '',
        ].filter(Boolean).join(' ');

        // Tooltip logic
        let tooltip = isLegal
            ? 'Click to move here'
            : isVisited
                ? 'Already visited'
                : 'Invalid move';
        if (isCurrent) tooltip = 'Current knight position';
        if (isStart && !isPreviewStart) tooltip = 'Start square';
        if (isPreviewStart) tooltip = 'Click to start here';

        return (
            <button
                key={key}
                className={classes}
                type="button"
                onClick={() => {
                    if (!isManualReady || isLegal || activePath.length === 0) {
                        onCellClick(cell);
                    }
                }}
                aria-label={tooltip}
                tabIndex={isCurrent ? 0 : -1}
                style={{ transition: 'box-shadow 0.2s, background 0.2s' }}
                disabled={isDisabled}
                title={tooltip}
            >
                <span className="cell-label">{moveIndex !== undefined ? moveIndex + 1 : `${row + 1},${col + 1}`}</span>
                {isCurrent && (
                    <span className={isDark ? 'cell-knight-shell cell-knight-shell-dark knight-animate' : 'cell-knight-shell cell-knight-shell-light knight-animate'}>
                        <img className="cell-knight" src={knightIcon} alt="Knight current position" title="Current knight position" aria-hidden="true" />
                    </span>
                )}
                {isPreviewStart && <span className="cell-tag">Start here</span>}
                {isStart && !isPreviewStart && <span className="cell-tag">Start</span>}
                {isCurrent && <span className="cell-tag cell-tag-current">You are here</span>}
                {isLegal && isManualReady && <span className="cell-ring cell-legal-animate" />}
                {isLastMove && <span className="move-highlight" />}
            </button>
        );
    }

    return (
        <div className="board-frame" ref={boardRef} aria-label="Chessboard" role="grid">
            <div
                className="board"
                style={{ gridTemplateColumns: `repeat(${boardSize}, minmax(0, 1fr))` }}
                role="rowgroup"
            >
                {Array.from({ length: boardSize }).flatMap((_, row) =>
                    Array.from({ length: boardSize }, (_, col) => renderCell(row, col)),
                )}
            </div>
            {/* Start hint */}
            {manualPathLength === 0 && (
                <div className="start-hint">Click any square to start</div>
            )}
        </div>
    );
}

export default Board;
