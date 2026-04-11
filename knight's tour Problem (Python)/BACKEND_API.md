# Knight's Tour - Backend API Integration

## New Feature: Backend Solver API

The Knight's Tour game now includes a **Python backend API** that handles knight tour solving. This provides several benefits:

### Benefits
- **Persistent Storage**: Save winners to SQLite database (backend)
- **Centralized Computing**: Use Python's optimized algorithms on the backend
- **Fallback Support**: If backend is unavailable, the frontend uses local browser solvers
- **Scalable**: Can handle more complex computations server-side

---

## Running the Application

### Prerequisites
- Python 3.10+
- Node.js 18+
- pip

### Setup

1. **Install backend dependencies:**
   ```bash
   pip install flask flask-cors
   cd backend && pip install -e .
   cd ..
   ```

2. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   ```

### Running the App

**Terminal 1 - Start Backend API (Port 5000):**
```bash
python run_api.py
```

Expected output:
```
Starting Knight's Tour API server...
Server running at http://localhost:5000/
* Running on http://0.0.0.0:5000
```

**Terminal 2 - Start Frontend Dev Server (Port 5173+):**
```bash
cd frontend
npm run dev
```

Expected output:
```
VITE v5.4.21 ready in XXX ms
➜  Local:   http://localhost:5173/
```

---

## API Endpoints

### `POST /api/solve`
Solve a knight tour problem.

**Request Body:**
```json
{
  "size": 8,
  "solver": "warnsdorff",
  "startRow": 0,
  "startCol": 0,
  "nodeLimit": 3500000
}
```

**Response:**
```json
{
  "valid": true,
  "reason": "Full tour found",
  "coverage": 1.0,
  "moves": 64,
  "path": [[0,0], [1,2], [2,0], ...]
}
```

### `GET /api/winners`
Get all saved winners from database.

**Response:**
```json
{
  "winners": [
    {
      "player": "Alice",
      "size": 8,
      "path": [[0,0], ...],
      "coverage": 1.0,
      "moves": 64,
      "timestamp": "2026-04-11T10:30:00",
      "solver": "warnsdorff"
    }
  ]
}
```

### `POST /api/winners`
Save a new winner.

**Request Body:**
```json
{
  "player": "Bob",
  "size": 8,
  "path": [[0,0], ...],
  "coverage": 1.0,
  "moves": 64,
  "solver": "warnsdorff"
}
```

### `GET /api/health`
Check if API is running.

**Response:**
```json
{"status": "ok"}
```

---

## Frontend-Backend Communication

The frontend (`frontend/src/api.ts`) automatically:
1. **Tries backend first** - Attempts to solve using `/api/solve`
2. **Fallback to browser** - If backend is offline, uses JavaScript solvers
3. **Saves results** - Sends winners to backend database when possible

### How It Works
1. User clicks "Start Tour" with auto-solver selected
2. Frontend calls `APIService.solve()`
3. Backend Flask API receives request → Uses Python algorithms
4. Backend returns solution `path` and `coverage`
5. Frontend animates the move sequence
6. Winner is saved to backend database via `APIService.saveWinner()`

---

## Troubleshooting

### "Connection refused" error
- Make sure backend is running: `python run_api.py`
- Check port 5000 is not blocked

### CORS errors
- Backend has CORS enabled for `localhost:517[3-6]`
- If running on different port, update `CORS` config in `backend/knighttour/api.py`

### No winners showing
- Check SQLite database at `backend/` directory
- Winners are stored in local database, not synced with browser localStorage

---

## Code Changes Made

1. **`backend/knighttour/api.py`** - NEW: Flask API server with solver endpoints
2. **`frontend/src/api.ts`** - NEW: TypeScript service for backend communication
3. **`frontend/src/App.tsx`** - UPDATED: Uses `APIService.solve()` instead of local solvers
4. **`pyproject.toml`** - UPDATED: Added Flask dependencies, API server entry point
5. **`run_api.py`** - NEW: Convenient launcher script for the backend

---

## Architecture Overview

```
┌─────────────────────────────────────┐
│   Browser (Frontend - React)        │
│  ┌──────────────────────────────┐  │
│  │ App.tsx (coordinator)        │  │
│  │  + APIService (api.ts)       │  │
│  │  + Local Solvers (fallback)  │  │
│  └──────────────────────────────┘  │
│  Runs on: localhost:5173+           │
└──────────────────┬──────────────────┘
                   │ HTTP
                   └──────────────────────┐
                                          │
                   ┌──────────────────────▼──────────────┐
                   │  Backend (Flask API - Python)      │
                   │  ┌────────────────────────────────┐│
                   │  │ /api/solve                     ││
                   │  │ - Warnsdorff solver            ││
                   │  │ - Backtracking solver          ││
                   │  │ /api/winners                   ││
                   │  │ - Save results to SQLite       ││
                   │  │ - Retrieve winner records      ││
                   │  └────────────────────────────────┘│
                   │  Runs on: localhost:5000           │
                   └──────────────────────────────────────┘
```

---

## Next Steps

Possible enhancements:
- [ ] Add WebSocket for real-time progress updates
- [ ] Implement user authentication and leaderboard
- [ ] Add difficulty levels based on board size
- [ ] Mobile app integration
- [ ] Deployment to production (Docker, cloud hosting)
