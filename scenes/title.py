"""Title and mission setup: crew, difficulty, destination, orbit, challenge codes."""
import pygame

from game import codes
from game import data as D
from game import render3d as R
from scenes import stack, ui
from scenes.base import Scene


class TitleScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.names = [ui.TextInput((0, 0, 150, 34), self.s["names"][i],
                                   "Player %d" % (i + 1)) for i in range(4)]
        self.code_in = ui.TextInput((0, 0, 190, 40), "", "MARS-7Q2K-9PX", limit=13, upper=True)
        self.build()

    # ---------------------------------------------------------------- layout
    def build(self):
        s = self.s
        b = []
        x0 = 60
        for n in range(1, 5):
            b.append(ui.Button((x0 + 150 + (n - 1) * 52, 182, 44, 36), str(n),
                               on=lambda n=n: self.set("player_count", n),
                               selected=s["player_count"] == n, size=17))
        for i in range(4):
            self.names[i].rect.topleft = (x0 + 380 + i * 160, 183)
        for i, key in enumerate(D.DIFFICULTY_ORDER):
            info = D.DIFFICULTIES[key]
            b.append(ui.Button((x0 + 150 + i * 232, 252, 222, 54), info["name"],
                               on=lambda k=key: self.set("difficulty", k),
                               selected=s["difficulty"] == key, sub=info["blurb"], size=16))
        for i, key in enumerate(D.MISSION_ORDER):
            m = D.MISSIONS[key]
            b.append(ui.Button((x0 + 150 + i * 232, 330, 222, 100), m["name"].split(":")[0],
                               on=lambda k=key: self.set_mission(k),
                               selected=s["mission"] == key, size=20, kind="title",
                               sub="$%dM  sun %d%%  %s" % (m["budget"], m["sunlight"] * 100,
                                                          m["difficulty"])))
        for i, oid in enumerate(D.MISSIONS[s["mission"]]["orbits"]):
            o = D.ORBITS[oid]
            sub = "science x%.2g  %d yr%s" % (o["science_x"], o["lifetime"],
                                              "  needs lander" if o["landing"] else "")
            b.append(ui.Button((x0 + 150 + i * 348, 456, 338, 54), o["name"],
                               on=lambda k=oid: self.set("orbit", k),
                               selected=s["orbit"] == oid, sub=sub, size=16))
        b.append(ui.Button((x0, 560, 360, 64), "START MISSION  >", on=self.start, size=22,
                           selected=True))
        self.code_in.rect.topleft = (x0 + 400, 572)
        b.append(ui.Button((x0 + 600, 572, 110, 40), "LOAD CODE", on=self.load_code, size=13))
        self.buttons = b

    def set(self, key, value):
        self.s[key] = value
        self.build()

    def set_mission(self, key):
        self.s["mission"] = key
        if self.s["orbit"] not in D.MISSIONS[key]["orbits"]:
            self.s["orbit"] = D.MISSIONS[key]["orbits"][-1]
        self.build()

    # ---------------------------------------------------------------- actions
    def start(self):
        self.s["names"] = [t.value.strip() for t in self.names]
        self.app.new_mission()
        self.app.go("hangar")

    def load_code(self):
        try:
            design, seed, cards = codes.decode(self.code_in.value)
        except ValueError as err:
            self.say(str(err), D.RED)
            return
        s = self.s
        s["mission"], s["orbit"] = design["mission"], design["orbit"]
        s["difficulty"] = design["difficulty"]
        s["names"] = [t.value.strip() for t in self.names]
        self.app.new_mission()
        s["design"] = design
        s["fixed_seed"] = seed
        s["cards"] = cards
        self.app.go("hangar", note="Challenge loaded: same design, same luck. Beat the score!")

    # ---------------------------------------------------------------- loop
    def handle(self, e):
        for i, t in enumerate(self.names[:self.s["player_count"]]):
            if t.handle(e):
                return
        if self.code_in.handle(e):
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                self.load_code()
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self.start()
            return
        super().handle(e)

    def draw(self, surf):
        s = self.s
        self.app.stars.draw(surf, self.t)
        # spinning real-mission spacecraft on the right
        m = s["mission"]
        nasa = D.NASA[m]
        d = D.empty_design(m, nasa["orbit"])
        d.update(nasa["design"])
        parts, top = stack.build(d, rocket_on=False, spin=self.t * 0.5)
        cam = R.make_camera(360, 720, yaw=0.5, pitch=0.32, dist=6.4, target=(0, top * 0.45, 0))
        sub = surf.subsurface((910, 0, 360, 720))
        pygame.draw.circle(sub, (22, 30, 40), (180, 360), 158)
        pygame.draw.circle(sub, ui.EDGE, (180, 360), 158, 1)
        ui.draw_faces(sub, R.render(parts, cam))
        ui.text(surf, "REAL MISSION", (1090, 548), 12, D.DIM, "bold", anchor="center")
        ui.text(surf, nasa["mission"], (1090, 570), 16, D.CREAM, "title", anchor="center")
        ui.text(surf, nasa["when"], (1090, 594), 13, D.HUD, anchor="center")

        # title
        ui.text(surf, "MISSION ARCHITECT", (58, 42), 54, D.CREAM, "title")
        ui.text(surf, "3D", (628, 42), 54, D.ORANGE, "title")
        ui.text(surf, "NASA SPACE APPS 2026  /  CHALLENGE 13  /  DESIGN. LAUNCH. LEARN.",
                (62, 118), 14, D.HUD)
        labels = [(196, "1  CREW"), (279, "2  LEVEL"), (360, "3  WHERE"), (483, "4  ORBIT")]
        for y, lab in labels:
            ui.text(surf, lab, (60, y), 14, D.ORANGE, "bold", anchor="midleft")
        for i, t in enumerate(self.names[:s["player_count"]]):
            t.draw(surf, self.t)
        mi = D.MISSIONS[m]
        ui.text(surf, "Goal: " + mi["goal"], (210, 438), 13, D.CREAM)
        self.code_in.draw(surf, self.t)
        ui.text(surf, "Got a challenge code from a friend?", (460, 618), 12, D.DIM)
        ui.text(surf, "Up to 4 players share one screen. Each role controls part of the "
                "spacecraft and holds a secret goal.", (60, 660), 13, D.DIM)
        ui.text(surf, "F9 demo seed   /   Enter to start", (60, 684), 12, (60, 70, 80))
        self.draw_buttons(surf)
        for i, key in enumerate(D.MISSION_ORDER):  # a little planet on each card
            cx, cy = 60 + 150 + i * 232 + 186, 368
            col = D.MISSIONS[key]["color"]
            pygame.draw.circle(surf, ui.mix(col, D.SPACE, 0.55), (cx + 3, cy + 3), 22)
            pygame.draw.circle(surf, col, (cx, cy), 22)
            pygame.draw.circle(surf, ui.mix(col, (255, 255, 255), 0.35), (cx - 7, cy - 7), 7)
            if key == "europa":
                pygame.draw.line(surf, (150, 110, 80), (cx - 18, cy + 4), (cx + 16, cy - 8), 2)
        self.draw_toast(surf)
