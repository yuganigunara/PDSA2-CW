import React from "react";
import { useEffect, useMemo, useState } from "react";

const API_BASE = "http://127.0.0.1:8002/api";

function delay(ms) {
    return new Promise((resolve) => {
        window.setTimeout(resolve, ms);
    });
}

async function waitForHttpReady(url, timeoutMs = 25000) {
    const deadline = Date.now() + timeoutMs;

    while (Date.now() < deadline) {
        try {
            // no-cors lets us detect network reachability without requiring CORS headers.
            await fetch(url, { method: "GET", mode: "no-cors", cache: "no-store" });
            return true;
        } catch {
            await delay(700);
        }
    }

    return false;
}

function App() {
    const [games, setGames] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    const [welcome, setWelcome] = useState("");
    const [activeLaunchIndex, setActiveLaunchIndex] = useState(-1);
    const [celebrateTick, setCelebrateTick] = useState(0);
    const [query, setQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");
    const [launchingIndex, setLaunchingIndex] = useState(-1);
    const [lastPlayedIndex, setLastPlayedIndex] = useState(() => {
        const raw = window.localStorage.getItem("gameHub:lastPlayedIndex");
        return raw ? Number(raw) : -1;
    });

    const enabledCount = useMemo(
        () => games.filter((game) => game.enabled).length,
        [games]
    );
    const disabledCount = games.length - enabledCount;
    const filteredGames = useMemo(() => {
        return games
            .map((game, index) => ({ game, index }))
            .filter(({ game }) => {
                const name = String(game?.name || "").toLowerCase();
                const folder = String(game?.cwd || "").toLowerCase();
                const matchesQuery =
                    !query.trim() || name.includes(query.toLowerCase()) || folder.includes(query.toLowerCase());

                if (!matchesQuery) {
                    return false;
                }

                if (statusFilter === "enabled") {
                    return Boolean(game?.enabled);
                }

                if (statusFilter === "disabled") {
                    return !Boolean(game?.enabled);
                }

                return true;
            });
    }, [games, query, statusFilter]);

    useEffect(() => {
        if (lastPlayedIndex < 0) {
            return;
        }

        if (lastPlayedIndex >= games.length) {
            setLastPlayedIndex(-1);
            window.localStorage.removeItem("gameHub:lastPlayedIndex");
        }
    }, [games, lastPlayedIndex]);

    async function loadGames() {
        setLoading(true);
        setError("");
        try {
            const response = await fetch(`${API_BASE}/games`);
            if (!response.ok) {
                throw new Error("Failed to load games");
            }
            const data = await response.json();
            setGames(Array.isArray(data.games) ? data.games : []);
        } catch (fetchError) {
            setError(fetchError.message);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadGames();
    }, []);

    useEffect(() => {
        const intervalId = window.setInterval(() => {
            loadGames();
        }, 5000);

        return () => {
            window.clearInterval(intervalId);
        };
    }, []);

    function getQuickLaunchUrl(game) {
        const name = String(game?.name || "").toLowerCase();
        const command = (game?.command || []).join(" ").toLowerCase();

        if (name.includes("traffic") || command.includes("traffic simulation") || command.includes("run.py")) {
            return "http://127.0.0.1:5000/";
        }

        if (name.includes("studio") || command.includes("run_studio.py")) {
            return "http://localhost:5173/";
        }

        return "";
    }

    async function launchGame(index) {
        const game = games[index] || {};
        const gameName = game?.name || `Game Slot ${index + 1}`;

        if (!game?.enabled || !game?.cwd || !(game?.command || []).length) {
            setError(`Slot ${index + 1} is not ready. Please configure it first.`);
            return;
        }

        setNotice("");
        setError("");
        setWelcome(`Welcome to ${gameName}`);
        setActiveLaunchIndex(index);
        setLaunchingIndex(index);
        setCelebrateTick((value) => value + 1);
        window.setTimeout(() => setActiveLaunchIndex(-1), 1700);
        setLastPlayedIndex(index);
        window.localStorage.setItem("gameHub:lastPlayedIndex", String(index));

        fetch(`${API_BASE}/games/${index}/launch`, {
            method: "POST",
        })
            .then(async (response) => {
                const data = await response.json();
                if (!response.ok) {
                    const detail = data?.detail;
                    if (typeof detail === "string") {
                        throw new Error(detail);
                    }
                    throw new Error(detail?.error || detail?.message || "Launch failed");
                }

                if (!data?.pid) {
                    throw new Error("Launch failed: no process ID returned");
                }

                setNotice(`${data.message} (PID: ${data.pid})`);
                setLaunchingIndex(-1);

                const quickUrl = data?.web_url || getQuickLaunchUrl(game);
                if (quickUrl) {
                    const ready = await waitForHttpReady(quickUrl);
                    if (ready) {
                        window.open(`${quickUrl}?fromHub=1`, "_blank", "noopener");
                    } else {
                        setNotice(
                            `${data.message} (PID: ${data.pid}). Web UI is still starting; open ${quickUrl} manually in a few seconds.`
                        );
                    }
                }
            })
            .catch((launchError) => {
                setError(launchError.message);
                setLaunchingIndex(-1);
            });
    }

    function launchFirstFiltered() {
        if (!filteredGames.length) {
            return;
        }
        launchGame(filteredGames[0].index);
    }

    function launchLastPlayed() {
        if (lastPlayedIndex < 0) {
            setNotice("No recently played game yet.");
            return;
        }
        launchGame(lastPlayedIndex);
    }

    return (
        <div className={`page celebrate-${celebrateTick % 2}`}>
            <div className="hero-orb hero-orb-left" />
            <div className="hero-orb hero-orb-right" />
            <div className="spark spark-1" />
            <div className="spark spark-2" />
            <div className="spark spark-3" />

            <header className="topbar">
                <div>
                    <h1>Game Hub Control Deck</h1>
                    <p>One software experience for all 5 game slots.</p>
                    {welcome && <p className="welcome-banner">{welcome}</p>}
                </div>
                <div className="topbar-actions">
                    <div className="stat-badge">
                        <span>{enabledCount}</span>
                        <small>enabled slots</small>
                    </div>
                    <div className="stat-badge muted-stat">
                        <span>{disabledCount}</span>
                        <small>waiting setup</small>
                    </div>
                    <button className="refresh-button" onClick={loadGames}>
                        Refresh
                    </button>
                </div>
            </header>

            <main>
                {loading && <p className="message">Loading game slots...</p>}
                {error && <p className="message error">{error}</p>}
                {notice && <p className="message ok">{notice}</p>}

                <section className="toolbar">
                    <input
                        className="search-input"
                        value={query}
                        onChange={(event) => setQuery(event.target.value)}
                        onKeyDown={(event) => {
                            if (event.key === "Enter") {
                                launchFirstFiltered();
                            }
                        }}
                        placeholder="Search game or folder..."
                    />
                    <div className="filter-tabs">
                        <button
                            className={`tab-btn ${statusFilter === "all" ? "active" : ""}`}
                            onClick={() => setStatusFilter("all")}
                        >
                            All
                        </button>
                        <button
                            className={`tab-btn ${statusFilter === "enabled" ? "active" : ""}`}
                            onClick={() => setStatusFilter("enabled")}
                        >
                            Enabled
                        </button>
                        <button
                            className={`tab-btn ${statusFilter === "disabled" ? "active" : ""}`}
                            onClick={() => setStatusFilter("disabled")}
                        >
                            Waiting Setup
                        </button>
                    </div>
                </section>

                <section className="quick-row">
                    <button className="tab-btn" onClick={launchLastPlayed}>
                        Play Last Game
                    </button>
                    <button
                        className="tab-btn"
                        onClick={() => {
                            setQuery("");
                            setStatusFilter("all");
                        }}
                    >
                        Clear Filters
                    </button>
                    <button
                        className="tab-btn logs-btn"
                        onClick={() => window.open("/logs.html", "_blank")}
                    >
                        📊 View Logs
                    </button>
                    <small className="results-note">Showing {filteredGames.length} of {games.length} slots</small>
                </section>

                <section className="grid">
                    {filteredGames.map(({ game, index }) => (
                        <article
                            className={`card ${activeLaunchIndex === index ? "card-launch" : ""}`}
                            key={`${game.name}-${index}`}
                            style={{ animationDelay: `${index * 70}ms` }}
                        >
                            <div className="card-head">
                                <h2>{game.name || `Game Slot ${index + 1}`}</h2>
                                <span className={game.enabled ? "pill on" : "pill off"}>
                                    {game.enabled ? "Enabled" : "Disabled"}
                                </span>
                            </div>

                            <p className="slot-id">Slot {index + 1}</p>
                            <p className="meta">Folder: {game.cwd || "not set"}</p>
                            <p className="meta">Command: {(game.command || []).join(" ") || "not set"}</p>

                            <div className="actions">
                                <button
                                    onClick={() => launchGame(index)}
                                    disabled={
                                        launchingIndex === index || !game.enabled || !game.cwd || !(game.command || []).length
                                    }
                                >
                                    {launchingIndex === index ? "Launching..." : game.enabled ? "Play Now" : "Setup Needed"}
                                </button>
                            </div>
                            {!game.enabled && (
                                <p className="setup-hint">Enable this slot and set folder/command to launch.</p>
                            )}
                        </article>
                    ))}
                </section>

                {!loading && filteredGames.length === 0 && (
                    <p className="message">No games match this filter. Try clearing search or choose All.</p>
                )}
            </main>
        </div>
    );
}

export default App;
