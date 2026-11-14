"""The Go/No-Go poll: every role votes before launch, like real mission control."""
import pygame

from game import data as D
from game import engine as E
from game import team
from scenes import ui
from scenes.base import Scene


def role_status(role, design):
    """One line each role would check before saying Go."""
    meters = {m[0]: m for m in E.meters(design)}
    if role == "director":
        o = D.ORBITS[design["orbit"]]
        return "%s, %d yr design life" % (o["name"], o["lifetime"]), "ok"
    if role == "engineer":
        _, v, _, st = meters["Mass"]
        _, pv, _, pst = meters["Power"]
        worst = "bad" if "bad" in (st, pst) else ("warn" if "warn" in (st, pst) else "ok")
        return "%s  |  %s" % (v, pv.split(" made")[0] + " made"), worst
    if role == "science":
        n = len(design["instruments"])
        return "%d instrument%s, %.0f Gb/day" % (n, "" if n == 1 else "s",
                                                 E.data_made(design)), "ok"
    _, v, _, st = meters["Budget"]
    _, dv, _, dst = meters["Data"]
    worst = "bad" if "bad" in (st, dst) else ("warn" if "warn" in (st, dst) else "ok")
    return "%s  |  %s" % (v, dv.split(", ")[1]), worst


class GoNoGoScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.votes = {}
        self.picking = None  # role choosing a No-Go reason
        self.done = None
        self.build()

    def owner(self, role):
        for p in self.s["players"]:
            if role in p["roles"]:
                return p["name"]
        return ""

    def build(self):
        b = []
        for i, role in enumerate(D.ROLES):
            x = 40 + i * 302
            voted = self.votes.get(role)
            b.append(ui.Button((x + 16, 400, 126, 56), "GO", on=lambda r=role: self.vote(r, True),
                               selected=voted is not None and voted[0], accent=D.HUD, size=22,
                               enabled=self.done is None))
            b.append(ui.Button((x + 150, 400, 126, 56), "NO-GO",
                               on=lambda r=role: self.vote(r, False),
                               selected=voted is not None and not voted[0], accent=D.RED,
                               size=18, enabled=self.done is None))
        if self.picking:
            for j, why in enumerate(team.NO_GO_REASONS):
                b.append(ui.Button((340 + (j % 2) * 304, 520 + (j // 2) * 46, 296, 38), why,
                                   on=lambda w=why: self.reason(w), size=12, accent=D.RED))
        if len(self.s["players"]) == 1 and self.done is None:
            b.append(ui.Button((1000, 640, 240, 48), "ALL ROLES GO", on=self.all_go, size=15,
                               accent=D.HUD))
        if self.done is not None:
            ok, _ = self.done
            if ok:
                b.append(ui.Button((480, 620, 320, 64), "LAUNCH  >",
                                   on=lambda: self.app.go("launch"), selected=True, size=24))
            else:
                b.append(ui.Button((480, 620, 320, 64), "BACK TO THE HANGAR",
                                   on=lambda: self.app.go("hangar"), size=18))
        b.append(ui.Button((40, 640, 180, 48), "< HANGAR", on=lambda: self.app.go("hangar"),
                           size=14))
        self.buttons = b

    def vote(self, role, go):
        if go:
            self.votes[role] = (True, "")
            if self.picking == role:
                self.picking = None
        else:
            self.picking = role
        self.check()

    def reason(self, why):
        self.votes[self.picking] = (False, why)
        self.picking = None
        self.check()

    def all_go(self):
        for r in D.ROLES:
            self.votes[r] = (True, "")
        self.picking = None
        self.check()

    def check(self):
        if len(self.votes) == len(D.ROLES) and not self.picking:
            self.done = team.go_no_go(self.votes)
        self.build()

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN and self.done and self.done[0]:
            self.app.go("launch")
            return
        super().handle(e)

    def draw(self, surf):
        self.app.stars.draw(surf, self.t, 1)
        ui.text(surf, "GO / NO-GO POLL", (640, 52), 40, D.CREAM, "title", anchor="center")
        ui.text(surf, "Flight Director calls the roll. Every role must say GO before launch.",
                (640, 100), 15, D.HUD, anchor="center")
        d = self.s["design"]
        for i, role in enumerate(D.ROLES):
            x = 40 + i * 302
            info = D.ROLE_INFO[role]
            r = ui.panel(surf, (x, 140, 292, 330), info["name"].upper(), info["color"])
            ui.text(surf, self.owner(role), (x + 146, 196), 20, D.CREAM, "title",
                    anchor="center")
            line, st = role_status(role, d)
            ui.text_box(surf, line, (x + 16, 240, 260, 60), 13, ui.state_color(st))
            ui.text(surf, "Your card: " + self.s["cards"][role]["text"]
                    if len(self.s["players"]) == 1 else "Check your secret card first",
                    (x + 16, 318), 11, D.DIM)
            v = self.votes.get(role)
            if v:
                col = D.HUD if v[0] else D.RED
                ui.text(surf, "GO" if v[0] else "NO-GO", (x + 146, 360), 24, col, "bold",
                        anchor="center")
                if not v[0]:
                    ui.text(surf, v[1], (x + 146, 384), 11, D.RED, anchor="center")
            elif self.picking == role:
                ui.text(surf, "Why? Pick a reason below", (x + 146, 370), 13, D.YELLOW,
                        anchor="center")
            else:
                ui.text(surf, "waiting...", (x + 146, 370), 13, D.DIM, anchor="center")
        if self.done is not None:
            ok, reasons = self.done
            if ok:
                ui.text(surf, "ALL STATIONS GO. YOU ARE CLEARED FOR LAUNCH.", (640, 520), 22,
                        D.HUD, "bold", anchor="center")
            else:
                ui.text(surf, "LAUNCH SCRUBBED", (640, 506), 26, D.RED, "bold", anchor="center")
                for j, why in enumerate(reasons[:3]):
                    ui.text(surf, why, (640, 542 + j * 22), 14, D.CREAM, anchor="center")
                ui.text(surf, "Negotiate, change the design, then poll again.", (640, 600), 12,
                        D.DIM, anchor="center")
        self.draw_buttons(surf)
        self.draw_toast(surf)
