"""The flight map: transfer arc across the solar system, one phase at a time.

Each phase's event plays as an effect: flare, radiation, dust, night,
rough_landing, discovery.
"""
import math
import random

import pygame

from game import data as D
from scenes import ui
from scenes.base import Scene

PHASE_SECS = 3.4
SUN = (340, 360)
TILT = 0.5  # squash orbits so the map looks like a tilted plane
ORBIT_R = {"earth": 120, "mars": 200, "jupiter": 315}


def orbit_point(r, a):
    return (SUN[0] + math.cos(a) * r, SUN[1] + math.sin(a) * r * TILT)


class FlightScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.res = self.s["result"]
        self.phases = self.res["phases"]
        self.i = 0
        self.pt = 0.0
        self.rng = random.Random(self.s["seed"] + 99)
        self.parts = []
        m = self.s["design"]["mission"]
        self.target = {"moon": "earth", "mars": "mars", "europa": "jupiter"}[m]
        self.a_earth = 2.6
        self.a_target = self.a_earth + (0.0 if m == "moon" else math.pi * 0.85)
        self.build()

    def build(self):
        last = self.i >= len(self.phases) - 1
        self.buttons = [ui.Button((1000, 640, 240, 52), "DEBRIEF  >" if last else "NEXT PHASE  >",
                                  on=self.next, size=16, selected=last)]

    def next(self):
        if self.i >= len(self.phases) - 1:
            self.app.go("debrief")
        else:
            self.i += 1
            self.pt = 0.0
            self.parts = []
            self.build()

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.next()
            return
        super().handle(e)

    def update(self, dt):
        super().update(dt)
        self.pt += dt
        if self.pt > PHASE_SECS and self.i < len(self.phases) - 1:
            self.next()
        eff = self.phases[self.i]["effect"]
        w, h = ui.W, ui.H
        if eff == "dust" and len(self.parts) < 260:
            for _ in range(6):
                self.parts.append([self.rng.uniform(-200, w), self.rng.uniform(0, h),
                                   self.rng.uniform(220, 420), self.rng.uniform(-30, 30),
                                   self.rng.uniform(2, 5)])
        if eff == "discovery" and len(self.parts) < 120 and self.pt < 2:
            sx, sy = self.ship()
            for _ in range(4):
                a = self.rng.random() * 2 * math.pi
                sp = self.rng.uniform(30, 160)
                self.parts.append([sx, sy, math.cos(a) * sp, math.sin(a) * sp, 3])
        for p in self.parts:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
        self.parts = [p for p in self.parts if -250 < p[0] < w + 50 and -50 < p[1] < h + 50]

    # ship position along the transfer arc
    def progress(self):
        base = {"Launch": 0.0, "Cruise": 0.15, "Arrival": 0.85, "Science": 1.0}
        ph = self.phases[self.i]["phase"]
        nxt = {"Launch": 0.15, "Cruise": 0.85, "Arrival": 1.0, "Science": 1.0}[ph]
        k = min(1.0, self.pt / (PHASE_SECS * 0.8))
        k = k * k * (3 - 2 * k)
        return base[ph] + (nxt - base[ph]) * k

    def target_pos(self):
        if self.target == "earth":
            e = orbit_point(ORBIT_R["earth"], self.a_earth)
            return (e[0] + 46, e[1] - 14)
        return orbit_point(ORBIT_R[self.target], self.a_target)

    def ship(self):
        k = self.progress()
        e = orbit_point(ORBIT_R["earth"], self.a_earth)
        t = self.target_pos()
        if self.target == "earth":
            return (e[0] + (t[0] - e[0]) * k, e[1] + (t[1] - e[1]) * k - math.sin(k * math.pi) * 30)
        r0, r1 = ORBIT_R["earth"], ORBIT_R[self.target]
        a = self.a_earth + (self.a_target - self.a_earth) * k
        r = r0 + (r1 - r0) * (1 - math.cos(k * math.pi)) / 2
        return orbit_point(r, a)

    # ---------------------------------------------------------------- draw
    def draw(self, surf):
        ph = self.phases[self.i]
        eff = ph["effect"]
        shake = (0, 0)
        if eff == "rough_landing" and self.pt < 1.2:
            shake = (self.rng.randint(-8, 8), self.rng.randint(-8, 8))
        self.app.stars.draw(surf, self.t, 2)
        mapsurf = surf
        # orbits
        for name, r in ORBIT_R.items():
            rect = pygame.Rect(0, 0, r * 2, r * 2 * TILT)
            rect.center = (SUN[0] + shake[0], SUN[1] + shake[1])
            pygame.draw.ellipse(mapsurf, (36, 52, 60), rect, 1)
        # sun
        pulse = 1.0
        if eff == "flare":
            pulse = 1.0 + 0.5 * abs(math.sin(self.pt * 6))
        for k in range(5, 0, -1):
            pygame.draw.circle(mapsurf, ui.mix(D.SPACE, D.GOLD, 0.15 * (6 - k)),
                               (SUN[0] + shake[0], SUN[1] + shake[1]), int(18 * pulse + k * 7))
        pygame.draw.circle(mapsurf, D.GOLD, (SUN[0] + shake[0], SUN[1] + shake[1]), int(22 * pulse))
        # planets
        e = orbit_point(ORBIT_R["earth"], self.a_earth)
        pygame.draw.circle(mapsurf, (70, 130, 200), (int(e[0]), int(e[1])), 11)
        ui.text(mapsurf, "EARTH", (e[0], e[1] + 18), 11, D.DIM, "bold", anchor="center")
        tp = self.target_pos()
        col = D.MISSIONS[self.s["design"]["mission"]]["color"]
        if self.target == "jupiter":
            pygame.draw.circle(mapsurf, (200, 160, 120), (int(tp[0]), int(tp[1])), 30)
            for k in (-8, 0, 9):
                pygame.draw.line(mapsurf, (170, 120, 90), (tp[0] - 28, tp[1] + k),
                                 (tp[0] + 28, tp[1] + k), 2)
            eu = (tp[0] + 48 * math.cos(self.t * 0.8), tp[1] + 18 * math.sin(self.t * 0.8))
            pygame.draw.circle(mapsurf, col, (int(eu[0]), int(eu[1])), 6)
            ui.text(mapsurf, "JUPITER + EUROPA", (tp[0], tp[1] + 44), 11, D.DIM, "bold",
                    anchor="center")
            if eff == "radiation":
                for k in range(3):
                    rr = int(40 + ((self.pt * 60 + k * 30) % 90))
                    pygame.draw.circle(mapsurf, D.PURPLE, (int(tp[0]), int(tp[1])), rr, 2)
        else:
            pygame.draw.circle(mapsurf, col, (int(tp[0]), int(tp[1])), 9 if self.target == "earth"
                               else 10)
            ui.text(mapsurf, D.MISSIONS[self.s["design"]["mission"]]["short"],
                    (tp[0], tp[1] + 18), 11, D.DIM, "bold", anchor="center")
        # transfer arc (dotted) and ship
        for k in range(0, 41):
            pts = self.arc_point(k / 40)
            if k % 2 == 0:
                pygame.draw.circle(mapsurf, D.TEAL, (int(pts[0]), int(pts[1])), 2)
        sx, sy = self.ship()
        sx, sy = sx + shake[0], sy + shake[1]
        pygame.draw.polygon(mapsurf, D.CREAM, [(sx, sy - 8), (sx + 6, sy + 6), (sx - 6, sy + 6)])
        pygame.draw.circle(mapsurf, D.HUD, (int(sx), int(sy)), 14, 1)

        # effects on top of the map
        if eff == "flare":
            a = 120 * max(0, 1 - self.pt / 2.2)
            ui.overlay(surf, D.ORANGE, a)
            for k in range(14):
                ang = k * math.pi / 7 + self.pt
                pygame.draw.line(surf, D.GOLD, SUN, (SUN[0] + math.cos(ang) * 900,
                                                     SUN[1] + math.sin(ang) * 900), 1)
        elif eff == "radiation":
            ui.overlay(surf, D.PURPLE, 40 + 40 * abs(math.sin(self.pt * 4)))
        elif eff == "dust":
            ui.overlay(surf, D.DUST, min(130, self.pt * 80))
            for p in self.parts:
                pygame.draw.circle(surf, (200, 140, 90), (int(p[0]), int(p[1])), int(p[4]))
        elif eff == "night":
            ui.overlay(surf, (4, 6, 20), min(190, self.pt * 120))
            if int(self.t * 3) % 2 == 0:
                pygame.draw.circle(surf, D.HUD if ph["prevented"] else D.RED,
                                   (int(sx), int(sy)), 4)
        elif eff == "discovery":
            for p in self.parts:
                pygame.draw.polygon(surf, D.GOLD, ui.star_shape(p[0], p[1], 5))
        elif eff == "rough_landing" and self.pt < 0.6:
            ui.overlay(surf, (255, 255, 255), 80 * (1 - self.pt / 0.6))

        self.draw_panel(surf, ph)
        self.draw_status(surf)
        self.draw_buttons(surf)
        self.draw_toast(surf)

    def arc_point(self, k):
        e = orbit_point(ORBIT_R["earth"], self.a_earth)
        t = self.target_pos()
        if self.target == "earth":
            return (e[0] + (t[0] - e[0]) * k, e[1] + (t[1] - e[1]) * k - math.sin(k * math.pi) * 30)
        r0, r1 = ORBIT_R["earth"], ORBIT_R[self.target]
        a = self.a_earth + (self.a_target - self.a_earth) * k
        r = r0 + (r1 - r0) * (1 - math.cos(k * math.pi)) / 2
        return orbit_point(r, a)

    def draw_status(self, surf):
        """Spacecraft status: instruments go dark when an event destroys them."""
        d = self.s["design"]
        r = ui.panel(surf, (700, 110, 540, 290), "SPACECRAFT STATUS")
        dead = set()
        for k, p in enumerate(self.phases[:self.i + 1]):
            if k < self.i or self.pt > 0.8:
                dead.update(p.get("lost", []))
        y = r.y + 42
        for iid in d["instruments"]:
            gone = iid in dead
            col = D.RED if gone else D.HUD
            pygame.draw.circle(surf, col, (r.x + 26, y + 9), 6, 0 if not gone else 2)
            ui.text(surf, D.INSTRUMENTS[iid]["name"], (r.x + 42, y), 15,
                    D.DIM if gone else D.CREAM)
            ui.text(surf, "LOST" if gone else "ONLINE", (r.right - 20, y), 13, col, "bold",
                    anchor="topright")
            y += 30
        hit = [p for p in self.phases[:self.i + 1] if p["effect"] in ("dust", "night")
               and not p["prevented"]]
        pw = "POWER: " + (D.POWER[d["power"]]["name"] if d["power"] else "none")
        if hit and (len(hit) > 1 or self.phases.index(hit[0]) < self.i or self.pt > 0.8):
            pw += "  /  REDUCED BY " + hit[-1]["event"].upper()
        ui.text(surf, pw, (r.x + 20, r.bottom - 54), 12, D.YELLOW if hit else D.DIM, "bold")
        ui.text(surf, "COMMS: " + (D.COMMS[d["comms"]]["name"] if d["comms"] else "none"),
                (r.x + 20, r.bottom - 32), 12, D.DIM, "bold")

    def draw_panel(self, surf, ph):
        # phase timeline across the top
        ui.text(surf, D.MISSIONS[self.s["design"]["mission"]]["name"].upper(), (40, 30), 22,
                D.CREAM, "title")
        x0 = 680
        step = min(150, 540 // max(1, len(self.phases) - 1))
        for k, p in enumerate(self.phases):
            x = x0 + k * step
            done = k < self.i
            cur = k == self.i
            col = D.DIM
            if done or cur:
                col = D.HUD if (p["prevented"] or not p["bad"]) else D.RED
            pygame.draw.circle(surf, col, (x, 44), 10 if cur else 7, 0 if done or cur else 1)
            if k < len(self.phases) - 1:
                pygame.draw.line(surf, D.DIM, (x + 12, 44), (x + step - 12, 44), 1)
            ui.text(surf, p["phase"].upper(), (x, 64), 11, col if cur else D.DIM, "bold",
                    anchor="center")
        # event card
        good = ph["prevented"] or not ph["bad"]
        accent = D.HUD if good else D.RED
        if ph["bad"] and ph["prevented"]:
            accent = D.TEAL
        r = ui.panel(surf, (700, 420, 540, 200), "%s  /  %s" % (ph["phase"].upper(),
                                                               ph["event"].upper()), accent)
        status = "NO PROBLEM" if not ph["bad"] else ("PREVENTED" if ph["prevented"] else "DAMAGE")
        ui.text(surf, status, (r.right - 14, r.y + 14), 12, D.SPACE, "bold", anchor="midright")
        ui.text_box(surf, ph["message"], (r.x + 18, r.y + 42, r.w - 36, 140), 17, D.CREAM,
                    "mono", gap=8)

