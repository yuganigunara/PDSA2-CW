# Game Hub React App

User-friendly gaming launcher with React frontend and FastAPI backend.

## What you get

- 5 game slots in one software dashboard
- Launch, enable/disable, configure each slot
- Clean structure with separated frontend and backend
- Uses your existing `game_hub_config.json` at workspace root

## Folder structure

```text
game-hub-react/
  backend/
    app/
      main.py
    requirements.txt
  frontend/
    src/
      App.jsx
      main.jsx
      styles.css
    index.html
    package.json
  README.md
```

## First-time setup (Windows)

From workspace root run:

```powershell
setup_game_hub.bat
```

## Start the app

From workspace root run:

```powershell
run_game_hub.bat
```

This starts:

- API server: `http://127.0.0.1:8000`
- React UI: `http://127.0.0.1:5173`

## Configure slots 4 and 5

Use the `Configure` button in the UI or edit `game_hub_config.json` manually.

Command examples:

- `{python} main.py`
- `{python} -m mygame.gui`

`cwd` must be relative to workspace root (`E:/PDSAgame`).
