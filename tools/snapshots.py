"""Renders every screen to PNG without opening a window.

Run from the project folder:  python tools/snapshots.py [out_dir]
Useful for checking layouts and for README screenshots.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MA3D_NO_FILE", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from game import data as D  # noqa: E402
from scenes import ui  # noqa: E402
from scenes.app import App  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "snapshots"


def mars_design(power="rtg", difficulty="engineer"):
    d = D.empty_design("mars", "mars_rover", difficulty)
    d.update(rocket="medium", power=power, comms="relay",
             instruments=["spectro", "drill", "radar", "camera"], protection=["land_mars"])
    return d


def run(app, secs, dt=1 / 30):
    for _ in range(int(secs / dt)):
        app.scene.update(dt)


def shot(app, name):
    app.scene.draw(app.screen)
    ui.scanlines(app.screen)
    pygame.image.save(app.screen, os.path.join(OUT, name + ".png"))
    print("saved", name)


def main():
    os.makedirs(OUT, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((ui.W, ui.H))
    app = App(screen)

    run(app, 1.0)
    shot(app, "01_title")

    # team of 3 on Mars
    s = app.s
    s["player_count"], s["names"] = 3, ["Jordan", "Ana", "Sam", ""]
    s["mission"], s["orbit"] = "mars", "mars_rover"
    app.new_mission()
    s["design"] = mars_design("solar_l")
    s["fixed_seed"] = 10
    app.go("hangar")
    run(app, 0.5)
    shot(app, "02_hangar_team")
    app.scene.set_cat("instruments")
    shot(app, "03_hangar_locked")
    app.scene.peek = True
    shot(app, "04_goal_card")
    app.scene.peek = False

    app.go("gonogo")
    app.scene.vote("director", True)
    app.scene.vote("engineer", True)
    app.scene.vote("science", False)
    shot(app, "05_gonogo_reason")
    app.scene.reason("Not enough power")
    app.scene.vote("comms", True)
    shot(app, "06_gonogo_scrub")

    app.go("launch")
    run(app, 1.2)
    shot(app, "07_countdown")
    run(app, 3.3)
    shot(app, "08_liftoff")
    run(app, 1.7)
    shot(app, "09_staging")

    app.go("flight")
    run(app, 1.5)
    shot(app, "10_flight_launch")
    for i in range(1, len(app.scene.phases)):
        app.scene.next()
        run(app, 1.6)
        shot(app, "11_flight_%d_%s" % (i, app.scene.phases[i]["effect"]))

    app.go("debrief")
    run(app, 2.0)
    shot(app, "12_debrief_solar")
    # same seed, nuclear: the pitch demo
    s["design"] = mars_design("rtg")
    app.go("launch")
    app.go("debrief")
    run(app, 2.0)
    shot(app, "13_debrief_nuclear")
    for v in ("report", "patch", "board"):
        app.scene.open(v)
        shot(app, "14_" + v)
        app.scene.close()

    # Europa without shielding, and an overweight Moon lander
    s["player_count"] = 1
    s["mission"], s["orbit"], s["difficulty"] = "europa", "europa_low", "cadet"
    app.new_mission()
    d = s["design"]
    d.update(rocket="heavy", power="solar_g", comms="hga",
             instruments=["radar", "magneto", "spectro", "thermal"], protection=[])
    s["fixed_seed"] = 3
    app.go("hangar")
    shot(app, "15_hangar_europa_cadet")
    app.go("launch")
    app.go("flight")
    while app.scene.i < len(app.scene.phases) - 1 and \
            app.scene.phases[app.scene.i]["effect"] != "radiation":
        app.scene.next()
    run(app, 1.5)
    shot(app, "16_flight_radiation")

    s["mission"], s["orbit"], s["difficulty"] = "moon", "south_lander", "engineer"
    app.new_mission()
    s["design"].update(rocket="small", power="solar_l", comms="small_ant",
                       instruments=["camera"], protection=["land_moon"])
    app.go("launch")
    run(app, 5.6)
    shot(app, "17_too_heavy")
    app.go("debrief")
    run(app, 2)
    shot(app, "18_debrief_lost")


if __name__ == "__main__":
    main()
