from __future__ import annotations

import os
import socket
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def launch_hidden(command: list[str], cwd: Path) -> None:
    creationflags = 0
    startupinfo = None
    if sys.platform.startswith("win"):
        creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        startupinfo = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]

    subprocess.Popen(
        command,
        cwd=str(cwd),
        creationflags=creationflags,
        startupinfo=startupinfo,
    )


def main() -> None:
    py_exe = sys.executable

    if not is_port_open("127.0.0.1", 5000):
        launch_hidden([py_exe, "run_api.py"], ROOT)

    if not is_port_open("127.0.0.1", 5173):
        launch_hidden(["cmd", "/c", "npm run dev -- --host localhost --port 5173"], FRONTEND)

    if os.environ.get("GAME_HUB_LAUNCH") != "1":
        webbrowser.open("http://localhost:5173/")


if __name__ == "__main__":
    main()
