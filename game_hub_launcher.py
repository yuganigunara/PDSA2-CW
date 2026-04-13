from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "game_hub_config.json"


DEFAULT_GAMES = [
    {
        "name": "Snake and Ladder",
        "cwd": "snake",
        "command": ["{python}", "main.py"],
        "enabled": True,
        "needs_src_path": False,
    },
    {
        "name": "Knight's Tour Studio",
        "cwd": "knight's tour Problem (Python)",
        "command": ["{python}", "run_studio.py"],
        "enabled": True,
        "needs_src_path": False,
    },
    {
        "name": "Traffic Simulation",
        "cwd": "Traffic simulation Problem",
        "command": ["{python}", "run.py"],
        "enabled": True,
        "needs_src_path": False,
    },
    {
        "name": "Game Slot 4",
        "cwd": "",
        "command": [],
        "enabled": False,
        "needs_src_path": False,
    },
    {
        "name": "Game Slot 5",
        "cwd": "",
        "command": [],
        "enabled": False,
        "needs_src_path": False,
    },
]


class GameHub(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Gaming Hub - 5 Game Launcher")
        self.geometry("860x480")
        self.minsize(760, 420)

        self.games = self._load_config()
        self.processes: list[subprocess.Popen[str]] = []

        self._build_ui()
        self._refresh_table()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=12)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Game Hub",
            font=("Segoe UI", 20, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            header,
            text="Launch all your games from one app. Edit slot 4 and 5 to add more games.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        table_wrap = ttk.Frame(self, padding=(12, 0, 12, 0))
        table_wrap.grid(row=1, column=0, sticky="nsew")
        table_wrap.columnconfigure(0, weight=1)
        table_wrap.rowconfigure(0, weight=1)

        self.table = ttk.Treeview(
            table_wrap,
            columns=("name", "status", "cwd", "command"),
            show="headings",
            selectmode="browse",
        )
        self.table.grid(row=0, column=0, sticky="nsew")

        self.table.heading("name", text="Game")
        self.table.heading("status", text="Status")
        self.table.heading("cwd", text="Working Folder")
        self.table.heading("command", text="Command")

        self.table.column("name", width=180, anchor="w")
        self.table.column("status", width=100, anchor="center")
        self.table.column("cwd", width=250, anchor="w")
        self.table.column("command", width=300, anchor="w")

        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical", command=self.table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.configure(yscrollcommand=scrollbar.set)

        actions = ttk.Frame(self, padding=12)
        actions.grid(row=2, column=0, sticky="ew")

        ttk.Button(actions, text="Launch Selected", command=self.launch_selected).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Configure Selected", command=self.configure_selected).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Enable/Disable", command=self.toggle_selected).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Save Config", command=self.save_config).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Exit", command=self._exit_app).pack(side="right")

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status_var, padding=(12, 0, 12, 12)).grid(row=3, column=0, sticky="w")

        self.table.bind("<Double-1>", lambda _event: self.launch_selected())

    def _load_config(self) -> list[dict]:
        if not CONFIG_PATH.exists():
            self._save_config_data(DEFAULT_GAMES)
            return [dict(item) for item in DEFAULT_GAMES]

        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Config must be a list")

            normalized = []
            for index in range(5):
                fallback = dict(DEFAULT_GAMES[index])
                source = data[index] if index < len(data) and isinstance(data[index], dict) else {}
                fallback.update(source)
                normalized.append(fallback)
            return normalized
        except Exception:
            messagebox.showwarning("Config warning", "Invalid config found. Default configuration restored.")
            self._save_config_data(DEFAULT_GAMES)
            return [dict(item) for item in DEFAULT_GAMES]

    def _save_config_data(self, games: list[dict]) -> None:
        CONFIG_PATH.write_text(json.dumps(games, indent=2), encoding="utf-8")

    def _refresh_table(self) -> None:
        self.table.delete(*self.table.get_children())
        for i, game in enumerate(self.games):
            status = "Enabled" if game.get("enabled") else "Disabled"
            command = " ".join(game.get("command") or [])
            self.table.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    game.get("name", f"Game Slot {i + 1}"),
                    status,
                    game.get("cwd", ""),
                    command,
                ),
            )

    def _selected_index(self) -> int | None:
        item = self.table.selection()
        if not item:
            messagebox.showinfo("Select a game", "Please select a game slot.")
            return None
        return int(item[0])

    def launch_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            return

        game = self.games[index]
        if not game.get("enabled"):
            messagebox.showwarning("Disabled", "This game slot is disabled. Enable it first.")
            return

        cwd_rel = game.get("cwd", "")
        command = game.get("command", [])

        if not cwd_rel or not command:
            messagebox.showerror("Not configured", "This slot is missing folder or command.")
            return

        cwd = ROOT_DIR / cwd_rel
        if not cwd.exists():
            messagebox.showerror("Missing folder", f"Folder not found:\n{cwd}")
            return

        command = [token.replace("{python}", sys.executable) for token in command]

        env = dict(os.environ)
        python_paths: list[str] = [str(cwd)]
        if game.get("needs_src_path"):
            python_paths.append(str(cwd / "src"))

        current = env.get("PYTHONPATH", "")
        joined = ";".join(python_paths)
        env["PYTHONPATH"] = joined if not current else f"{joined};{current}"

        try:
            process = subprocess.Popen(command, cwd=str(cwd), env=env, text=True)
            self.processes.append(process)
            self.status_var.set(f"Launched: {game.get('name', 'Unknown')}")
        except Exception as exc:
            messagebox.showerror("Launch failed", f"Could not launch game.\n\n{exc}")

    def configure_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            return

        game = self.games[index]
        name = simpledialog.askstring("Game name", "Game name:", initialvalue=game.get("name", ""), parent=self)
        if name is None:
            return

        cwd = simpledialog.askstring(
            "Working folder",
            "Folder relative to workspace root (example: snake):",
            initialvalue=game.get("cwd", ""),
            parent=self,
        )
        if cwd is None:
            return

        cmd = simpledialog.askstring(
            "Launch command",
            "Command (use {python} for Python path). Example: {python} main.py",
            initialvalue=" ".join(game.get("command") or []),
            parent=self,
        )
        if cmd is None:
            return

        needs_src = messagebox.askyesno(
            "Needs src on PYTHONPATH?",
            "Should this game add <folder>/src to PYTHONPATH before launch?",
            parent=self,
        )

        game["name"] = name.strip() or f"Game Slot {index + 1}"
        game["cwd"] = cwd.strip()
        game["command"] = shlex.split(cmd.strip(), posix=False)
        game["needs_src_path"] = needs_src
        if game["command"] and game["cwd"]:
            game["enabled"] = True

        self._refresh_table()
        self.status_var.set(f"Updated: {game['name']}")

    def toggle_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            return

        game = self.games[index]
        game["enabled"] = not bool(game.get("enabled"))
        self._refresh_table()
        self.status_var.set(
            f"{game.get('name', 'Game')} is now {'Enabled' if game['enabled'] else 'Disabled'}."
        )

    def save_config(self) -> None:
        self._save_config_data(self.games)
        self.status_var.set(f"Config saved to: {CONFIG_PATH.name}")

    def _exit_app(self) -> None:
        self._save_config_data(self.games)
        self.destroy()


if __name__ == "__main__":
    app = GameHub()
    app.mainloop()
