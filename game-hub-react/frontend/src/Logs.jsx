import React, { useEffect, useState } from "react";
import "./Logs.css";

function Logs() {
    const [logs, setLogs] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 3000); // Refresh every 3 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchLogs = async () => {
        try {
            const response = await fetch("http://127.0.0.1:8002/api/logs");
            const data = await response.json();
            setLogs(data);
            setError("");
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="logs-container"><p>Loading...</p></div>;
    if (error) return <div className="logs-container error"><p>Error: {error}</p></div>;

    const ts = logs?.traffic_simulation || {};
    const kt = logs?.knights_tour || {};

    return (
        <div className="logs-container">
            <h1>🎮 Game Logs Dashboard</h1>
            <p className="timestamp">Last updated: {new Date(logs?.timestamp).toLocaleTimeString()}</p>

            <div className="logs-grid">
                {/* Traffic Simulation */}
                <div className="log-card">
                    <h2>🚗 Traffic Simulation</h2>

                    <div className="log-section">
                        <h3>Recent Rounds</h3>
                        {ts.error && <p className="error">{ts.error}</p>}
                        {!ts.error && ts.rounds?.length === 0 && <p>No rounds yet</p>}
                        {ts.rounds && ts.rounds.map((round, i) => (
                            <div key={i} className="log-entry">
                                <p><strong>Round {round.id}</strong></p>
                                <p>Max Flow: <span className="value">{round.correct_max_flow}</span></p>
                                <p>Ford-Fulkerson: <span className="time">{round.ff_time_ms.toFixed(4)}ms</span></p>
                                <p>Edmonds-Karp: <span className="time">{round.ek_time_ms.toFixed(4)}ms</span></p>
                                <p className="date">{new Date(round.created_at).toLocaleString()}</p>
                            </div>
                        ))}
                    </div>

                    <div className="log-section">
                        <h3>Leaderboard</h3>
                        {ts.wins && ts.wins.map((win, i) => (
                            <div key={i} className="leaderboard-entry">
                                <span className="rank">#{i + 1}</span>
                                <span className="name">{win.player_name}</span>
                                <span className="score">{win.wins_count} wins</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Knight's Tour */}
                <div className="log-card">
                    <h2>♞ Knight's Tour</h2>

                    <div className="log-section">
                        <h3>Recent Games</h3>
                        {kt.error && <p className="error">{kt.error}</p>}
                        {!kt.error && kt.games?.length === 0 && <p>No games yet</p>}
                        {kt.games && kt.games.map((game, i) => (
                            <div key={i} className="log-entry">
                                <p><strong>Game {game.id}</strong></p>
                                <p>Board Size: <span className="value">{game.board_size}x{game.board_size}</span></p>
                                <p>Mode: <span className="value">{game.mode}</span></p>
                                <p>Status: <span className="status">{game.status}</span></p>
                                <p className="date">{new Date(game.created_at).toLocaleString()}</p>
                            </div>
                        ))}
                    </div>

                    <div className="log-section">
                        <h3>Winners</h3>
                        {kt.winners && kt.winners.map((winner, i) => (
                            <div key={i} className="leaderboard-entry">
                                <span className="rank">#{i + 1}</span>
                                <span className="name">{winner.player_name}</span>
                                <span className="score">{winner.wins_count} wins</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Logs;
