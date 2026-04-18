# Game Hub Launcher

This launcher runs your games from one desktop app.

## Included by default

- Snake and Ladder
- Knight's Tour
- Traffic Simulation
- Game Slot 4 (empty, configurable)
- Game Slot 5 (empty, configurable)

## Run

From workspace root:

```powershell
python game_hub_launcher.py
```

Or double-click:

- `run_game_hub.bat`

## Fresh clone setup (important)

If you cloned this repository on a new machine, run setup first from workspace root:

```powershell
.\setup_game_hub.bat
.\run_game_hub.bat
```

Note: On first launch after clone/zip, some game UIs can take 10 to 30 seconds to become ready while dependencies/build cache initialize.

Prerequisites:

- Python 3.10+
- Node.js LTS (includes npm)

What setup does:

- Creates `E:/PDSAgame/.venv` if missing
- Installs Game Hub backend dependencies
- Installs Snake and Traffic Simulation dependencies
- Installs Knight's Tour Python package
- Installs both React frontends (`game-hub-react/frontend` and `knight's tour Problem (Python)/frontend`)

## How to add your 4th and 5th games

1. Start the launcher.
2. Select `Game Slot 4` or `Game Slot 5`.
3. Click `Configure Selected`.
4. Fill these values:
   - Game name
   - Working folder relative to workspace root
   - Launch command
5. Use `{python}` in the command for Python executable path.

Example commands:

- `{python} main.py`
- `{python} -m mygame.gui`

If your project uses `src` layout, choose `Yes` when asked to add `src` to `PYTHONPATH`.

## Save config

Click `Save Config` to write `game_hub_config.json`.

The app also auto-saves config when you exit.

## Direct linking by file edit (best for all 5 games)

Edit `game_hub_config.json` and fill `Game Slot 4` and `Game Slot 5`.

Each slot format:

```json
{
   "name": "My Game",
   "cwd": "folder_name",
   "command": ["{python}", "main.py"],
   "enabled": true,
   "needs_src_path": false
}
```

Notes:

- `cwd` is the folder path relative to `E:/PDSAgame`.
- `command` can be Python or non-Python command.
- Use `{python}` to auto-use your current Python environment.
- Set `needs_src_path` to `true` only for `src`-layout projects.
