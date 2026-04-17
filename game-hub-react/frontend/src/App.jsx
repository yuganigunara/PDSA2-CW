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

    const enabledCount = games.length;
    const filteredGames = useMemo(() => {
        return games
            .map((game) => ({ game, slotIndex: Number(game?.slotIndex ?? -1) }))
            .filter(({ game }) => {
                const name = String(game?.name || "").toLowerCase();
                const folder = String(game?.cwd || "").toLowerCase();
                const matchesQuery =
                    !query.trim() || name.includes(query.toLowerCase()) || folder.includes(query.toLowerCase());

                if (!matchesQuery) {
                    return false;
                }

                return true;
            });
    }, [games, query]);

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
            const loadedGames = Array.isArray(data.games)
                ? data.games
                    .map((game, slotIndex) => ({ ...game, slotIndex }))
                    .filter((game) => Boolean(game?.enabled))
                : [];
            setGames(loadedGames);
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

    async function launchGame(slotIndex) {
        const game = games.find((item) => Number(item?.slotIndex) === Number(slotIndex)) || {};
        const gameName = game?.name || `Game Slot ${Number(slotIndex) + 1}`;

        if (!game?.cwd || !(game?.command || []).length) {
            setError(`Slot ${Number(slotIndex) + 1} is not ready. Please configure it first.`);
            return;
        }

        setNotice("");
        setError("");
        setWelcome(`Welcome to ${gameName}`);
        setActiveLaunchIndex(slotIndex);
        setLaunchingIndex(slotIndex);
        setCelebrateTick((value) => value + 1);
        window.setTimeout(() => setActiveLaunchIndex(-1), 1700);
        setLastPlayedIndex(slotIndex);
        window.localStorage.setItem("gameHub:lastPlayedIndex", String(slotIndex));

        fetch(`${API_BASE}/games/${slotIndex}/launch`, {
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
        launchGame(filteredGames[0].slotIndex);
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
                        <small>active games</small>
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
                    <div className="filter-tabs" />
                </section>

                <section className="quick-row">
                    <button className="tab-btn" onClick={launchLastPlayed}>
                        Play Last Game
                    </button>
                    <button
                        className="tab-btn"
                        onClick={() => {
                            setQuery("");
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
                    {filteredGames.map(({ game, slotIndex }) => (
                        <article
                            className={`card ${activeLaunchIndex === slotIndex ? "card-launch" : ""}`}
                            key={`${game.name}-${slotIndex}`}
                            style={{ animationDelay: `${slotIndex * 70}ms` }}
                        >
                            <div className="card-head">
                                <h2>{game.name || `Game Slot ${slotIndex + 1}`}</h2>
                                <span className="pill on">Enabled</span>
                            </div>

                            <p className="slot-id">Slot {slotIndex + 1}</p>
                            <p className="meta">Folder: {game.cwd || "not set"}</p>
                            <p className="meta">Command: {(game.command || []).join(" ") || "not set"}</p>

                            <div className="actions">
                                <button
                                    onClick={() => launchGame(slotIndex)}
                                    disabled={
                                        launchingIndex === slotIndex || !game.cwd || !(game.command || []).length
                                    }
                                >
                                    {launchingIndex === slotIndex ? "Launching..." : "Play Now"}
                                </button>
                            </div>
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
