"""Save and load small values.

In the browser (pygbag) this uses window.localStorage, so the leaderboard
survives a page reload. On the desktop it keeps a dict and also tries a
JSON file in the home folder. Values must be JSON-friendly.
"""
import json
import os
import sys

_MEM = {}
_LS = None
if sys.platform == "emscripten":
    try:
        import platform as _platform  # pygbag's browser bridge
        _LS = _platform.window.localStorage
    except Exception:
        _LS = None

_FILE = os.path.join(os.path.expanduser("~"), ".mission_architect_3d.json")
_PREFIX = "ma3d:"


def _desktop_load():
    if sys.platform == "emscripten":
        return
    try:
        with open(_FILE) as fh:
            _MEM.update(json.load(fh))
    except Exception:
        pass


def _desktop_save():
    if sys.platform == "emscripten" or os.environ.get("MA3D_NO_FILE"):
        return
    try:
        with open(_FILE, "w") as fh:
            json.dump(_MEM, fh)
    except Exception:
        pass


if not os.environ.get("MA3D_NO_FILE"):
    _desktop_load()


def save(key, value):
    text = json.dumps(value)
    if _LS is not None:
        try:
            _LS.setItem(_PREFIX + key, text)
            return
        except Exception:
            pass
    _MEM[key] = json.loads(text)
    _desktop_save()


def load(key, default=None):
    if _LS is not None:
        try:
            raw = _LS.getItem(_PREFIX + key)
            if raw is not None:
                return json.loads(str(raw))
            return default
        except Exception:
            pass
    return _MEM.get(key, default)


def clear():
    """Testing helper: forget everything held in memory."""
    _MEM.clear()
