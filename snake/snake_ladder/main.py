from __future__ import annotations

import argparse

from snake_ladder.game import SnakeAndLadderGame
from snake_ladder.gui import SnakeAndLadderGUI


def main() -> None:
    parser = argparse.ArgumentParser(description="Snake and Ladder Coursework")
    parser.add_argument(
        "--mode",
        choices=["gui", "cli"],
        default="gui",
        help="Run desktop GUI (default) or terminal CLI mode.",
    )
    args = parser.parse_args()

    if args.mode == "cli":
        game = SnakeAndLadderGame()
        game.run()
        return

    gui = SnakeAndLadderGUI()
    gui.run()


if __name__ == "__main__":
    main()
