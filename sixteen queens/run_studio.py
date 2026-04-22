from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
API_HOST = "127.0.0.1"
API_PORT = 8003
FRONTEND_PORT = 5190


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

    if not is_port_open(API_HOST, API_PORT):
        launch_hidden(
            [py_exe, "-m", "uvicorn", "main:app", "--host", API_HOST, "--port", str(API_PORT)],
            BACKEND,
        )

    npm_command = ["npm", "run", "dev", "--", "--host", "localhost", "--port", str(FRONTEND_PORT), "--strictPort"]
    if sys.platform.startswith("win"):
        npm_command = ["cmd", "/c", " ".join(npm_command)]

    if not is_port_open("127.0.0.1", FRONTEND_PORT):
        launch_hidden(npm_command, FRONTEND)


if __name__ == "__main__":
    main()
