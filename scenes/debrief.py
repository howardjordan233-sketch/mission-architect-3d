"""Debrief: score, You vs. NASA ghost, tip, goals, code, report, patch, leaderboard."""
import pygame

from game import codes
from game import data as D
from game import engine as E
from game import leaderboard
from game import patch
from game import render3d as R
from game import report
from scenes import patch_draw, stack, ui
from scenes.base import Scene

BAR_MAX = D.SCORE_SPLIT


def short(name):
    return name.split(" (")[0]


class DebriefScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        s = self.s
        d, res = s["design"], s["result"]
        self.sc = E.score(d, res, goals=self.app.goal_ids())
        s["score"] = self.sc
        self.code = codes.encode(d, s["seed"], s["cards"])
        s["code"] = self.code
        self.prev = s["history"][-1] if s["history"] else None
        s["history"].append(self.sc["total"])
        self.place = None
        if D.DIFFICULTIES[d["difficulty"]]["board"]:
            self.place = leaderboard.add(d["mission"], self.app.team_name(), self.sc["total"],
                                         self.sc["stars"], self.code)
        self.report = report.make_report(d, res, self.sc, cards=s["cards"],
                                         players=s["players"], code=self.code)
        self.patch = patch.patch_design(d, self.sc, self.app.team_name())
        self.view = None  # "report", "patch", "board"
        self.scroll = 0
        self.shown = 0.0
        self.build()

    def build(self):
        b = []
        if self.view:
            b.append(ui.Button((1080, 646, 170, 46), "CLOSE", on=self.close, size=15))
            if self.view == "patch":
                b.append(ui.Button((860, 646, 210, 46), "SAVE PATCH", on=self.save_patch,
                                   size=15, selected=True))
            if self.view == "report":
                b.append(ui.Button((860, 646, 210, 46), "SAVE REPORT", on=self.save_report,
                                   size=15, selected=True))
        else:
            row = [("TRY AGAIN", self.retry, True), ("NEW MISSION", self.new, False),
                   ("REPORT", lambda: self.open("report"), False),
                   ("PATCH", lambda: self.open("patch"), False),
                   ("LEADERBOARD", lambda: self.open("board"), False)]
            for i, (lab, fn, sel) in enumerate(row):
                b.append(ui.Button((16 + i * 252, 646, 240, 56), lab, on=fn, selected=sel,
                                   size=16))
        self.buttons = b

    def open(self, v):
        self.view, self.scroll = v, 0
        self.build()

    def close(self):
        self.view = None
        self.build()

    def retry(self):
        self.app.go("hangar", note="Same design. Change one thing and fly again.")

    def new(self):
        self.app.go("title")

    def save_patch(self):
        self.say(patch_draw.save_patch(self.patch, self.code), D.GOLD, 4)

    def save_report(self):
        self.say(patch_draw.save_text(self.report, "mission_report_%s.txt"
                                      % self.code.replace("-", "_")), D.GOLD, 4)

    def handle(self, e):
        if e.type == pygame.MOUSEWHEEL and self.view == "report":
            self.scroll = max(0, self.scroll - e.y * 3)
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and self.view:
            self.close()
            return
        super().handle(e)

    def update(self, dt):
        super().update(dt)
        self.shown = min(1.0, self.shown + dt * 0.8)

    # ---------------------------------------------------------------- draw
    def draw(self, surf):
        s, d, res, sc = self.s, self.s["design"], self.s["result"], self.sc
        m = D.MISSIONS[d["mission"]]
        nasa = D.NASA[d["mission"]]
        self.app.stars.draw(surf, self.t, 1)
        ui.text(surf, "MISSION DEBRIEF", (16, 14), 30, D.CREAM, "title")
        head = "MISSION LOST" if res["lost"] else ("MISSION SUCCESS" if sc["stars"] >= 3
                                                   else "MISSION COMPLETE")
        ui.text(surf, head, (1264, 22), 22, D.RED if res["lost"] else D.HUD, "bold",
                anchor="topright")
        ui.text(surf, "%s  /  %s  /  attempt %d" % (m["name"], D.ORBITS[d["orbit"]]["name"],
                                                    s["attempt"]), (18, 54), 13, D.DIM)

        # ---- score panel
        ui.panel(surf, (8, 80, 400, 552), "SCORE")
        shown = int(sc["total"] * self.shown)
        ui.text(surf, str(shown), (208, 190), 110, D.CREAM, "title", anchor="center")
        ui.text(surf, "/ 100", (208, 262), 16, D.DIM, anchor="center")
        ui.stars(surf, (208, 312), sc["stars"] if self.shown >= 1 else 0, 20, gap=46)
        y = 356
        labels = {"science": "Science", "budget": "Budget left", "reliability": "Reliability",
                  "goals": "Role goals"}
        for k in ("science", "budget", "reliability", "goals"):
            v, mx = sc["breakdown"][k], BAR_MAX[k]
            ui.meter(surf, (28, y, 360, 30), labels[k], "%d / %d" % (v, mx), v / mx * self.shown,
                     "ok" if v >= mx * 0.6 else ("warn" if v >= mx * 0.3 else "bad"))
            y += 44
        if self.prev is not None:
            dlt = sc["total"] - self.prev
            ui.text(surf, "%+d vs. your last try" % dlt, (28, y + 6), 14,
                    D.HUD if dlt >= 0 else D.RED, "bold")
        if self.place:
            ui.text(surf, "#%d on the %s leaderboard" % (self.place, m["short"].title()),
                    (28, y + 30), 14, D.GOLD, "bold")
        elif not D.DIFFICULTIES[d["difficulty"]]["board"]:
            ui.text(surf, "Sandbox runs don't go on the leaderboard", (28, y + 30), 12, D.DIM)

        # ---- You vs NASA 3D
        view = pygame.Rect(416, 80, 448, 552)
        sub = surf.subsurface(view)
        pygame.draw.rect(surf, (14, 18, 24), view, border_radius=8)
        ghost = D.empty_design(d["mission"], nasa["orbit"])
        ghost.update(nasa["design"])
        spin = self.t * 0.45
        mine, top1 = stack.build(d, rocket_on=False, x=-1.45, spin=spin)
        theirs, top2 = stack.build(ghost, rocket_on=False, ghost=True, x=1.45, spin=spin)
        top = max(top1, top2)
        cam = R.make_camera(view.w, view.h, yaw=0.0, pitch=0.28, dist=7.0,
                            target=(0, top * 0.45, 0))
        ui.grid_floor(sub, cam, size=4, color=(26, 46, 52))
        ui.draw_faces(sub, R.render(mine, cam))
        if getattr(self, "_ghost", None) is None:
            self._ghost = pygame.Surface(view.size, pygame.SRCALPHA)
        ghost_s = self._ghost
        ghost_s.fill((0, 0, 0, 0))
        ui.draw_faces(sub, R.render(theirs, cam, cull=False), alpha_surf=ghost_s)
        sub.blit(ghost_s, (0, 0))
        ui.text(surf, "YOU", (view.x + 110, view.y + 470), 18, D.CREAM, "title", anchor="center")
        ui.text(surf, "NASA", (view.x + 338, view.y + 470), 18, D.HUD, "title", anchor="center")
        ui.text(surf, nasa["mission"], (view.x + 338, view.y + 496), 12, D.HUD, anchor="center")
        ui.text(surf, "see-through ghost = the real design", (view.centerx, view.y + 530), 11,
                D.DIM, anchor="center")
        pygame.draw.rect(surf, ui.EDGE, view, 1, border_radius=8)

        # ---- comparison panel
        r = ui.panel(surf, (872, 80, 400, 552), "YOU VS. NASA", D.ORANGE)
        rows = [("Power", short(D.POWER[d["power"]]["name"]) if d["power"] else "none",
                 nasa["power"]),
                ("Rocket", D.ROCKETS[d["rocket"]]["name"].split(" (")[0] if d["rocket"] else "-",
                 nasa["rocket"]),
                ("Orbit", D.ORBITS[d["orbit"]]["name"], D.ORBITS[nasa["orbit"]]["name"]),
                ("Instruments", str(len(d["instruments"])),
                 str(len(nasa["design"]["instruments"])))]
        ui.text(surf, "YOU", (1010, 116), 11, D.DIM, "bold")
        ui.text(surf, "NASA", (1148, 116), 11, D.DIM, "bold")
        y = 138
        for lab, a, b in rows:
            ui.text(surf, lab, (888, y), 12, D.DIM, "bold")
            ui.text(surf, a[:17], (1010, y), 12, D.CREAM)
            ui.text(surf, b[:16], (1148, y), 12, D.HUD)
            y += 24
        y = ui.text_box(surf, "Lesson: " + nasa["lesson"], (888, y + 8, 368, 60), 13, D.CREAM)
        tip = D.TIPS[E.weakest_link(d, res)]
        ui.text(surf, "TIP FOR NEXT TIME", (888, y + 14), 11, D.ORANGE, "bold")
        y = ui.text_box(surf, tip, (888, y + 34, 368, 60), 13, D.CREAM)
        ui.text(surf, "ROLE GOALS  (+%d each)" % D.GOAL_POINTS, (888, y + 14), 11, D.GOLD, "bold")
        y += 34
        met = set(sc["goals_met"])
        for role, card in s["cards"].items():
            ok = card["id"] in met
            ui.text(surf, "[x]" if ok else "[ ]", (888, y), 12, D.HUD if ok else D.DIM, "bold")
            ui.text(surf, card["text"][:40], (920, y), 12, D.CREAM if ok else D.DIM)
            y += 20
        ui.text(surf, "CHALLENGE CODE", (1072, 566), 11, D.DIM, "bold", anchor="center")
        ui.text(surf, self.code, (1072, 596), 26, D.HUD, "bold", anchor="center")
        ui.text(surf, "a friend can fly this exact mission", (1072, 620), 10, D.DIM,
                anchor="center")

        if self.view:
            self.draw_view(surf)
        self.draw_buttons(surf)
        self.draw_toast(surf)

    def draw_view(self, surf):
        ui.overlay(surf, (0, 0, 0), 190)
        if self.view == "report":
            r = ui.panel(surf, (140, 40, 1000, 596), "MISSION REPORT", D.TEAL)
            lines = []
            for raw in self.report.split("\n"):
                lines.extend(ui.wrap(raw, 14, 950) or [""])
            visible = lines[self.scroll:self.scroll + 30]
            for i, line in enumerate(visible):
                ui.text(surf, line, (r.x + 22, r.y + 40 + i * 18), 14, D.CREAM)
            if len(lines) > 30:
                ui.text(surf, "scroll for more", (r.right - 16, r.bottom - 16), 11, D.DIM,
                        anchor="bottomright")
        elif self.view == "patch":
            patch_draw.draw_patch(surf, self.patch, (640, 330), 260)
        elif self.view == "board":
            mission = self.s["design"]["mission"]
            r = ui.panel(surf, (290, 60, 700, 560), "%s LEADERBOARD  /  TOP 10"
                         % D.MISSIONS[mission]["short"], D.GOLD)
            board = leaderboard.get(mission)
            if not board:
                ui.text(surf, "No runs yet. Be the first!", (640, 300), 18, D.CREAM, "title",
                        anchor="center")
            for i, e in enumerate(board):
                y = r.y + 56 + i * 46
                me = e.get("code") == self.code and e["score"] == self.sc["total"]
                col = D.GOLD if me else D.CREAM
                ui.text(surf, "%2d" % (i + 1), (r.x + 30, y), 22, col, "bold")
                ui.text(surf, e["name"], (r.x + 90, y + 2), 18, col, "title")
                ui.stars(surf, (r.x + 430, y + 14), e["stars"], 8, gap=19)
                ui.text(surf, str(e["score"]), (r.x + 540, y), 22, col, "bold")
                ui.text(surf, e.get("code", ""), (r.right - 24, y + 6), 12, D.DIM,
                        anchor="topright")
