from snake_ladder.algorithms import min_throws_bfs, min_throws_dp
from snake_ladder.board import BoardSetup


def test_bfs_and_dp_on_plain_board_size_6() -> None:
    board = BoardSetup(size=6, ladders={}, snakes={})

    bfs = min_throws_bfs(board)
    dp = min_throws_dp(board)

    assert bfs == 6
    assert dp == 6


def test_bfs_and_dp_with_ladder_and_snake() -> None:
    board = BoardSetup(
        size=6,
        ladders={2: 15, 8: 20},
        snakes={30: 12, 26: 5},
    )

    bfs = min_throws_bfs(board)
    dp = min_throws_dp(board)

    assert bfs == dp
    assert bfs > 0
