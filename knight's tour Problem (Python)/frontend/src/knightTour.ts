export type SolverMode = 'warnsdorff' | 'backtracking';

export interface Position {
    row: number;
    col: number;
}

export interface ValidationResult {
    valid: boolean;
    reason: string;
    coverage: number;
}

export interface WinnerRecord {
    player: string;
    size: number;
    start: string;
    pathLength: number;
    timestamp: string;
    sequence: string[];
}

const OFFSETS: ReadonlyArray<readonly [number, number]> = [
    [2, 1],
    [2, -1],
    [-2, 1],
    [-2, -1],
    [1, 2],
    [1, -2],
    [-1, 2],
    [-1, -2],
];

export function positionKey(position: Position): string {
    return `${position.row},${position.col}`;
}

export function positionLabel(position: Position): string {
    return `(${position.row + 1}, ${position.col + 1})`;
}

export function isInsideBoard(size: number, row: number, col: number): boolean {
    return row >= 0 && row < size && col >= 0 && col < size;
}

export function isKnightMove(start: Position, end: Position): boolean {
    const dRow = Math.abs(start.row - end.row);
    const dCol = Math.abs(start.col - end.col);
    return (dRow === 2 && dCol === 1) || (dRow === 1 && dCol === 2);
}

export function getPossibleMoves(
    size: number,
    row: number,
    col: number,
    visited: Set<string> = new Set(),
): Position[] {
    const moves: Position[] = [];
    for (const [dRow, dCol] of OFFSETS) {
        const nextRow = row + dRow;
        const nextCol = col + dCol;
        const candidate = { row: nextRow, col: nextCol };
        if (isInsideBoard(size, nextRow, nextCol) && !visited.has(positionKey(candidate))) {
            moves.push(candidate);
        }
    }
    return moves;
}

function onwardCount(size: number, move: Position, visited: Set<string>): number {
    const nextVisited = new Set(visited);
    nextVisited.add(positionKey(move));
    return getPossibleMoves(size, move.row, move.col, nextVisited).length;
}

export function solveWarnsdorff(size: number, start: Position): Position[] | null {
    const visited = new Set<string>([positionKey(start)]);
    const path: Position[] = [start];

    while (path.length < size * size) {
        const current = path[path.length - 1];
        const candidates = getPossibleMoves(size, current.row, current.col, visited);
        if (candidates.length === 0) {
            return null;
        }

        candidates.sort((left, right) => onwardCount(size, left, visited) - onwardCount(size, right, visited));
        const chosen = candidates[0];
        path.push(chosen);
        visited.add(positionKey(chosen));
    }

    return path;
}

export function solveBacktracking(
    size: number,
    start: Position,
    nodeLimit = 3_500_000,
): Position[] | null {
    const visitedGrid: boolean[][] = Array.from({ length: size }, () => Array(size).fill(false));
    const visitedKeys = new Set<string>();
    const path: Position[] = [];
    let visitedNodes = 0;

    function dfs(row: number, col: number): boolean {
        visitedNodes += 1;
        if (visitedNodes > nodeLimit) {
            return false;
        }

        const position = { row, col };
        visitedGrid[row][col] = true;
        visitedKeys.add(positionKey(position));
        path.push(position);

        if (path.length === size * size) {
            return true;
        }

        const moves = getPossibleMoves(size, row, col, visitedKeys);
        moves.sort((left, right) => onwardCount(size, left, visitedKeys) - onwardCount(size, right, visitedKeys));

        for (const nextMove of moves) {
            if (!visitedGrid[nextMove.row][nextMove.col] && dfs(nextMove.row, nextMove.col)) {
                return true;
            }
        }

        visitedGrid[row][col] = false;
        visitedKeys.delete(positionKey(position));
        path.pop();
        return false;
    }

    return dfs(start.row, start.col) ? [...path] : null;
}

export function validatePath(size: number, path: Position[], start: Position): ValidationResult {
    if (path.length === 0) {
        return { valid: false, reason: 'Path is empty', coverage: 0 };
    }

    const target = size * size;
    if (path[0].row !== start.row || path[0].col !== start.col) {
        return {
            valid: false,
            reason: 'Path does not start at the required square',
            coverage: path.length / target,
        };
    }

    const visited = new Set<string>();
    for (let index = 0; index < path.length; index += 1) {
        const current = path[index];
        if (!isInsideBoard(size, current.row, current.col)) {
            return { valid: false, reason: `Move ${index + 1} is outside the board`, coverage: index / target };
        }

        const key = positionKey(current);
        if (visited.has(key)) {
            return { valid: false, reason: `Square repeated at move ${index + 1}`, coverage: index / target };
        }
        visited.add(key);

        if (index > 0 && !isKnightMove(path[index - 1], current)) {
            return { valid: false, reason: `Move ${index + 1} is not a legal knight move`, coverage: index / target };
        }
    }

    if (path.length !== target) {
        return { valid: false, reason: 'Path is incomplete', coverage: path.length / target };
    }

    return { valid: true, reason: 'Valid complete tour', coverage: 1 };
}
