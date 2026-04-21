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
    }, []);

    function getQuickLaunchUrl(game) {
        const name = String(game?.name || "").toLowerCase();
        const command = (game?.command || []).join(" ").toLowerCase();

        if (name.includes("snake")) {
            return "http://localhost:5176/";
        }

        if (name.includes("knight")) {
            return "http://localhost:5174/";
        }

        if (name.includes("sixteen")) {
            return "http://localhost:5190/";
        }

        if (name.includes("minimum cost")) {
            return "http://localhost:5187/";
        }

        if (name.includes("traffic") || command.includes("traffic simulation") || command.includes("run.py")) {
            return "http://127.0.0.1:5000/";
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

                // Prefer client-side mapping first so each game keeps its dedicated port.
                const quickUrl = getQuickLaunchUrl(game) || data?.web_url;
                if (quickUrl) {
                    const ready = await waitForHttpReady(quickUrl);
                    if (ready) {
                        window.open(`${quickUrl}?fromHub=1`, "_self");
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

    const staticNames = [
        "Snake Ladder Studio",
        "Knight's Tour Studio",
        "Traffic Simulation Studio",
        "Sixteen Queens Studio",
        "Minimum Cost Studio"
    ];

    return (
        <div className={`page celebrate-${celebrateTick % 2}`}>
            <div className="hero-orb hero-orb-left" />
            <div className="hero-orb hero-orb-right" />
            <div className="spark spark-1" />
            <div className="spark spark-2" />
            <div className="spark spark-3" />

            <header className="topbar">
                <div>
                    <h1>AlgoPlay Hub</h1>
                    <p>One interactive platform to solve complex algorithms through fun challenges</p>
                    {welcome && <p className="welcome-banner">{welcome}</p>}
                </div>

            </header>

            <main>
                {loading && <p className="message">Loading game slots...</p>}
                {error && <p className="message error">{error}</p>}
                {notice && <p className="message ok">{notice}</p>}


                <section className="grid">
                    {[0, 1, 2, 3, 4].map((slotIndex) => {
                        const descriptions = [
                            "Play the classic Snake & Ladder challenge-roll,climb,and win!",
                            "Solve the Knight's Tour puzzle with smart and strategic moves.",
                            "Simulate and optimize real-time traffic flow using powerful algorithms.",
                            "Master the Sixteen Queens puzzle with logical placement strategies.",
                            "Assign tasks efficiently and minimize total cost using smart optimization."
                        ];
                        return (
                            <article
                                className={`card ${activeLaunchIndex === slotIndex ? "card-launch" : ""}`}
                                key={`slot-${slotIndex}`}
                                style={{ animationDelay: `${slotIndex * 70}ms` }}
                            >
                                <div className="card-head">
                                    <h2>{staticNames[slotIndex]}</h2>
                                    <span className="pill on">Enabled</span>
                                </div>
                                <p className="slot-id">Slot {slotIndex + 1}</p>
                                <p className="meta">{descriptions[slotIndex]}</p>
                                <div className="actions">
                                    <button
                                        onClick={() => launchGame(slotIndex)}
                                        disabled={
                                            launchingIndex === slotIndex
                                        }
                                    >
                                        {launchingIndex === slotIndex ? "Launching..." : "Play Now"}
                                    </button>
                                </div>
                            </article>
                        );
                    })}
                </section>

                {!loading && filteredGames.length === 0 && (
                    <p className="message">No games match this filter. Try clearing search or choose All.</p>
                )}
            </main>
        </div>
    );
}

export default App;
