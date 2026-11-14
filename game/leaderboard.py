"""Top 10 per mission, kept through game.storage."""
from game import storage

SIZE = 10


def get(mission):
    return list(storage.load("board:" + mission, []))


def add(mission, name, points, stars, code=""):
    """Add a run. Returns its place (1-10) or None if it missed the board."""
    board = get(mission)
    entry = {"name": (name or "Anon")[:22], "score": int(points), "stars": int(stars),
             "code": code}
    board.append(entry)
    board.sort(key=lambda e: -e["score"])
    board = board[:SIZE]
    storage.save("board:" + mission, board)
    for i, e in enumerate(board):
        if e is entry:
            return i + 1
    return None
