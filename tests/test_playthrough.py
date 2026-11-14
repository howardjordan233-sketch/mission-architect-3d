"""Clicks through the whole game with real mouse events, headless.

Every mission x difficulty x team size: title -> hangar -> go/no-go ->
launch -> flight -> debrief -> try again -> new mission.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["MA3D_NO_FILE"] = "1"

import pygame  # noqa: E402
import pytest  # noqa: E402

from game import data as D  # noqa: E402
from game import storage  # noqa: E402
from scenes import ui  # noqa: E402
from scenes.app import App  # noqa: E402

PICKS = {
    "moon": {"rocket": "medium", "power": "solar_l", "instruments": ["drill", "spectro", "camera"],
             "comms": "small_ant", "protection": ["land_moon"], "battery": True},
    "mars": {"rocket": "medium", "power": "rtg", "instruments": ["spectro", "drill", "radar"],
             "comms": "relay", "protection": ["land_mars"], "battery": False},
    "europa": {"rocket": "heavy", "power": "solar_g",
               "instruments": ["radar", "magneto", "spectro"],
               "comms": "hga", "protection": ["shield"], "battery": False},
}
CADET_SAFE = {"spectro": "spectro", "drill": "radar", "camera": "camera", "magneto": "camera",
              "radar": "radar"}


@pytest.fixture(scope="module")
def screen():
    pygame.init()
    return pygame.display.set_mode((ui.W, ui.H))


def frames(app, n=3, dt=1 / 30):
    for _ in range(n):
        app.scene.update(dt)
        app.scene.draw(app.screen)


def click_label(app, label, startswith=False, nth=0):
    seen = 0
    for b in app.scene.buttons:
        name = b.label if not startswith else b.label[:len(label)]
        if name == label and b.enabled:
            if seen < nth:
                seen += 1
                continue
            pos = b.rect.center
            app.scene.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
            app.scene.handle(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))
            frames(app, 1)
            return True
    labels = [(b.label, b.enabled) for b in app.scene.buttons]
    raise AssertionError("no enabled button %r in %s: %s" % (label, type(app.scene).__name__,
                                                             labels))


def name_of(cat, pid):
    return D.part_info(cat, pid)["name"]


def build_in_hangar(app, mission):
    picks = dict(PICKS[mission])
    d = app.s["design"]
    if d["difficulty"] == "cadet":
        picks["instruments"] = list(dict.fromkeys(CADET_SAFE[i] for i in picks["instruments"]))
        if picks["power"] not in D.CADET_PARTS["power"]:
            picks["power"] = "solar_l"
    needed = {"rocket": [picks["rocket"]], "power": [picks["power"]],
              "instruments": picks["instruments"], "comms": [picks["comms"]],
              "protection": picks["protection"]}
    players = app.s["players"]
    for cat in D.CATEGORIES:
        # hand the laptop to whoever controls this category
        for _ in range(len(players)):
            if app.scene.can_edit(cat):
                break
            click_label(app, "PASS TO")
        assert app.scene.can_edit(cat)
        tab = {"rocket": "ROCKET", "power": "POWER", "instruments": "SCIENCE",
               "comms": "COMMS", "protection": "PROTECT"}[cat]
        click_label(app, tab)
        for pid in needed[cat]:
            click_label(app, name_of(cat, pid))
        if cat == "power" and picks["battery"]:
            click_label(app, "+ Battery pack", startswith=True)


@pytest.mark.parametrize("mission", D.MISSION_ORDER)
@pytest.mark.parametrize("difficulty", D.DIFFICULTY_ORDER)
@pytest.mark.parametrize("players", [1, 4])
def test_full_round(screen, mission, difficulty, players):
    storage.clear()
    app = App(screen)
    frames(app)
    click_label(app, str(players))
    click_label(app, D.DIFFICULTIES[difficulty]["name"])
    click_label(app, D.MISSIONS[mission]["name"].split(":")[0])
    click_label(app, "START MISSION  >")
    assert type(app.scene).__name__ == "HangarScene"
    assert len(app.s["players"]) == players
    build_in_hangar(app, mission)
    d = app.s["design"]
    assert d["rocket"] and d["power"] and d["instruments"] and d["comms"], d
    click_label(app, "LAUNCH  >")
    assert type(app.scene).__name__ == "GoNoGoScene"
    if players == 1:
        click_label(app, "ALL ROLES GO")
    else:
        # one No-Go first: the launch must scrub and send the team back
        click_label(app, "NO-GO")  # Flight Director
        click_label(app, "Not enough power")
        for k in (1, 2, 3):
            click_label(app, "GO", nth=k)
        click_label(app, "BACK TO THE HANGAR")
        assert type(app.scene).__name__ == "HangarScene"
        click_label(app, "LAUNCH  >")
        for k in range(4):
            click_label(app, "GO", nth=k)
    click_label(app, "LAUNCH  >")
    assert type(app.scene).__name__ == "LaunchScene"
    frames(app, 260, 1 / 30)  # let the launch play out on its own
    if type(app.scene).__name__ == "FlightScene":
        for _ in range(8):
            if type(app.scene).__name__ != "FlightScene":
                break
            frames(app, 20)
            label = app.scene.buttons[0].label
            click_label(app, label)
    assert type(app.scene).__name__ == "DebriefScene"
    sc = app.s["score"]
    assert 0 <= sc["total"] <= 100
    if difficulty == "sandbox":
        assert sc["stars"] >= 3, (mission, sc)
    for v in ("REPORT", "PATCH", "LEADERBOARD"):
        click_label(app, v)
        frames(app, 2)
        click_label(app, "CLOSE")
    click_label(app, "TRY AGAIN")
    assert type(app.scene).__name__ == "HangarScene"
    assert app.s["design"]["rocket"] == d["rocket"]  # design kept
    click_label(app, "MENU")
    assert type(app.scene).__name__ == "TitleScene"


def test_challenge_code_round_trip(screen):
    storage.clear()
    app = App(screen)
    click_label(app, "START MISSION  >")
    build_in_hangar(app, "mars")
    click_label(app, "LAUNCH  >")
    click_label(app, "ALL ROLES GO")
    click_label(app, "LAUNCH  >")
    frames(app, 260)
    while type(app.scene).__name__ == "FlightScene":
        click_label(app, app.scene.buttons[0].label)
    first = app.s["score"]["total"]
    code = app.s["code"]
    app.go("title")
    app.scene.code_in.value = code
    click_label(app, "LOAD CODE")
    assert type(app.scene).__name__ == "HangarScene"
    click_label(app, "LAUNCH  >")
    click_label(app, "ALL ROLES GO")
    click_label(app, "LAUNCH  >")
    frames(app, 260)
    while type(app.scene).__name__ == "FlightScene":
        click_label(app, app.scene.buttons[0].label)
    assert app.s["code"] == code
    assert app.s["score"]["total"] == first


def test_pitch_demo_is_identical_every_time(screen):
    """F9 demo: solar rover 66 (3 stars), nuclear rover 93 (5 stars), any team size."""
    for players in (1, 3):
        storage.clear()
        app = App(screen)
        app.toggle_demo()
        app.s["player_count"], app.s["mission"], app.s["orbit"] = players, "mars", "mars_rover"
        app.new_mission()
        totals = []
        for power in ("solar_l", "rtg"):
            app.s["design"].update(rocket="medium", power=power, comms="relay",
                                   instruments=["spectro", "drill", "radar", "camera"],
                                   protection=["land_mars"])
            app.go("launch")
            app.go("debrief")
            totals.append((app.s["score"]["total"], app.s["score"]["stars"]))
        assert totals == [(66, 3), (93, 5)], totals


def test_touch_taps_work(screen):
    """A tap arrives as finger events plus touch-made mouse events with a stale position.
    The game must act on the finger position and ignore the stale mouse events."""
    import importlib.util
    import pathlib
    spec = importlib.util.spec_from_file_location(
        "ma3d_main_mod", pathlib.Path(__file__).resolve().parent.parent / "main.py")
    src = spec.loader.get_source("ma3d_main_mod").replace("asyncio.run(main())", "")
    mod = {"__name__": "ma3d_main_mod"}
    exec(compile(src, "main.py", "exec"), mod)
    storage.clear()
    app = App(screen)
    start = next(b for b in app.scene.buttons if b.label.startswith("START MISSION"))
    x, y = start.rect.center
    raw = [
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0), touch=True),
        pygame.event.Event(pygame.FINGERDOWN, x=x / ui.W, y=y / ui.H, dx=0, dy=0,
                           touch_id=0, finger_id=0, pressure=1.0),
        pygame.event.Event(pygame.FINGERUP, x=x / ui.W, y=y / ui.H, dx=0, dy=0,
                           touch_id=0, finger_id=0, pressure=0.0),
        pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(0, 0), touch=True),
    ]
    for r in raw:
        for e in mod["translate"](r, app):
            app.scene.handle(e)
    assert type(app.scene).__name__ == "HangarScene"
    assert app.mouse_pos == (int(x / ui.W * ui.W), int(y / ui.H * ui.H))
