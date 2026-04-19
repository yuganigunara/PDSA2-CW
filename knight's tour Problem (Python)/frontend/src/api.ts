/**
 * API service for Knight's Tour backend.
 * Communicates with Flask API running on port 5001.
 */

const API_BASE = 'http://localhost:5001/api';

export interface WinnerRecordResponse {
    player: string;
    size: number;
    start: string;
    pathLength: number;
    timestamp: string;
    sequence: string[];
}

export interface SolveRequest {
    size: number;
    solver: 'warnsdorff' | 'backtracking';
    startRow: number;
    startCol: number;
    nodeLimit?: number;
}

export interface SolveResponse {
    valid: boolean;
    reason: string;
    coverage: number;
    moves: number;
    path: Array<[number, number]>;
}

export interface WinnerData {
    player: string;
    size: number;
    path: Array<[number, number]>;
    coverage: number;
    moves: number;
    solver: string;
}

export interface ScoreRecordResponse {
    player: string;
    size: number;
    start: string;
    score: number;
    result: 'win' | 'lose' | 'draw';
    timestamp: string;
}

export interface ScoreData {
    player: string;
    size: number;
    start: string;
    score: number;
    result: 'win' | 'lose' | 'draw';
}

export class APIService {
    /**
     * Check if backend API is available
     */
    static async checkHealth(): Promise<boolean> {
        try {
            const response = await fetch(`${API_BASE}/health`, { method: 'GET' });
            return response.ok;
        } catch {
            return false;
        }
    }

    /**
     * Solve knight tour using backend
     */
    static async solve(request: SolveRequest): Promise<SolveResponse> {
        const response = await fetch(`${API_BASE}/solve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Save a winner to the backend database
     */
    static async saveWinner(winner: WinnerData): Promise<void> {
        const response = await fetch(`${API_BASE}/winners`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(winner),
        });

        if (!response.ok) {
            throw new Error(`Failed to save winner: ${response.statusText}`);
        }
    }

    /**
     * Get all saved winners from backend
     */
    static async getWinners(): Promise<WinnerRecordResponse[]> {
        const response = await fetch(`${API_BASE}/winners`, { method: 'GET' });

        if (!response.ok) {
            throw new Error(`Failed to get winners: ${response.statusText}`);
        }

        const data = await response.json();
        return data.winners || [];
    }

    static async saveScore(score: ScoreData): Promise<void> {
        const response = await fetch(`${API_BASE}/scores`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(score),
        });

        if (!response.ok) {
            throw new Error(`Failed to save score: ${response.statusText}`);
        }
    }

    static async getScores(): Promise<ScoreRecordResponse[]> {
        const response = await fetch(`${API_BASE}/scores`, { method: 'GET' });

        if (!response.ok) {
            throw new Error(`Failed to get scores: ${response.statusText}`);
        }

        const data = await response.json();
        return data.scores || [];
    }
}
