from __future__ import annotations

import socket
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"


def is_port_open(host: str, port: int) -> bool:
    # Check both IPv4 and IPv6 so we do not spawn duplicate servers.
    for family, socktype, proto, _, sockaddr in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
        try:
            with socket.socket(family, socktype, proto) as sock:
                sock.settimeout(0.25)
                if sock.connect_ex(sockaddr) == 0:
                    return True
        except OSError:
            continue
    return False


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

    if not is_port_open("localhost", 5000):
        launch_hidden([py_exe, "run_api.py"], ROOT)

    if not is_port_open("localhost", 5173):
        launch_hidden(["cmd", "/c", "npm run dev -- --host localhost --port 5173"], FRONTEND)

    webbrowser.open("http://localhost:5173/")


if __name__ == "__main__":
    main()
