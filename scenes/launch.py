"""Liftoff: countdown, exhaust, staging. Too heavy means it wobbles and falls back."""
import math
import random

import pygame

from game import data as D
from game import events as V
from game import render3d as R
from scenes import stack, ui
from scenes.base import Scene

COUNT = 2.4  # T-3, T-2, T-1
STAGE = 2.4  # seconds after liftoff
LENGTH = COUNT + 5.0


class LaunchScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        s = self.s
        self.app.roll_seed()
        s["result"] = V.run_mission(s["design"], seed=s["seed"])
        s["attempt"] += 1
        first = s["result"]["phases"][0]
        self.fail = first["effect"] == "failure"
        self.heavy = s["result"].get("lost_reason") == "mass"
        self.smoke = []
        self.debris = []
        self.rng = random.Random(s["seed"])
        self.boom_at = None

    def handle(self, e):
        if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or \
                (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN)):
            if self.t > 0.6:
                self.finish()

    def finish(self):
        self.app.go("debrief" if self.s["result"]["lost"] else "flight")

    # rocket height and tilt over time
    def motion(self, t):
        lift = max(0.0, t - COUNT)
        if self.heavy:
            h = 1.2 * math.sin(min(math.pi, lift * 1.4)) if lift > 0 else 0
            tilt = 0.25 * math.sin(lift * 7) * min(1, lift)
            if lift > 1.8:
                tilt = min(1.4, (lift - 1.8) * 1.6)
                h = max(-0.2, h)
            return h, tilt
        if self.fail and lift > 1.6:
            return 0.5 * 1.6 ** 2 * 1.4, 0.0
        return 0.5 * lift ** 2 * 1.4, 0.0

    def update(self, dt):
        super().update(dt)
        lift = self.t - COUNT
        h, tilt = self.motion(self.t)
        boom = (self.heavy and lift > 2.3) or (self.fail and lift > 1.6)
        if boom and self.boom_at is None:
            self.boom_at = self.t
            for _ in range(140):
                a = self.rng.random() * 2 * math.pi
                sp = self.rng.uniform(40, 260)
                self.debris.append([0.0, 0.0, math.cos(a) * sp, math.sin(a) * sp - 80,
                                    self.rng.uniform(0.6, 1.6)])
        if 0 < lift and self.boom_at is None:
            for _ in range(5):
                self.smoke.append([self.rng.uniform(-18, 18), 0.0, self.rng.uniform(-30, 30),
                                   self.rng.uniform(60, 150), 1.0, h])
        for p in self.smoke:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt * 0.7
        self.smoke = [p for p in self.smoke if p[4] > 0][-400:]
        for p in self.debris:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 160 * dt
            p[4] -= dt
        self.debris = [p for p in self.debris if p[4] > 0]
        if self.t > LENGTH + (1.2 if self.boom_at else 0):
            self.finish()

    def draw(self, surf):
        d = self.s["design"]
        h, tilt = self.motion(self.t)
        lift = self.t - COUNT
        # sky gets darker as you climb
        sky = ui.mix((40, 60, 84), (10, 12, 22), min(1.0, h / 14))
        surf.fill(sky)
        self.app.stars.draw(surf, self.t, 0) if h > 6 else None
        stage_gap = max(0.0, (lift - STAGE)) if not (self.fail or self.heavy) else 0.0
        parts, top = stack.build(d)
        shown = []
        for p in parts:
            q = dict(p)
            if p.get("tag") in ("rocket",) and stage_gap > 0:
                q["y"] = p["y"] + h - stage_gap ** 2 * 1.5
                q["x"] = p.get("x", 0) + stage_gap * 0.4
            else:
                q["y"] = p["y"] + h
            if tilt:
                q["tilt"] = p.get("tilt", 0) + tilt
                q["x"] = q.get("x", 0) + math.sin(tilt) * (p["y"] + 1)
                q["y"] = q["y"] * math.cos(tilt)
            shown.append(q)
        follow = min(h, h * 0.9) + top * 0.45
        cam = R.make_camera(ui.W, ui.H, yaw=0.5 + self.t * 0.04, pitch=0.12,
                            dist=top * 1.5 + 4, target=(0, follow, 0))
        # ground and tower
        ground = [{"shape": "cylinder", "height": 0.5, "width": 3.4, "y": -0.5, "sides": 20,
                   "color": (58, 64, 62), "smooth": True},
                  {"shape": "cylinder", "height": 0.04, "width": 1.5, "y": 0.0, "sides": 20,
                   "color": D.ORANGE, "smooth": True},
                  {"shape": "cube", "height": top * 0.9, "width": 0.18, "x": -1.9,
                   "color": (96, 100, 108)},
                  {"shape": "cube", "height": 0.1, "width": 0.5, "sx": 0.8, "sz": 0.08,
                   "x": -1.3, "y": top * 0.8, "color": D.ORANGE}]
        if self.boom_at is None or self.t - self.boom_at < 0.15:
            ui.draw_faces(surf, R.render(ground + shown, cam))
        else:
            ui.draw_faces(surf, R.render(ground, cam))
        # exhaust and smoke, anchored at the base of the rocket
        base = R.project_point((0, h, 0), cam)
        if stage_gap > 0:  # the spent stage falls away; the craft fires its own engine
            base = R.project_point((0, h + top * 0.5, 0), cam)
        if base and lift > 0 and self.boom_at is None:
            fl = 30 + 12 * math.sin(self.t * 40)
            pygame.draw.polygon(surf, D.GOLD, [(base[0] - 14, base[1]), (base[0] + 14, base[1]),
                                               (base[0], base[1] + fl * 2.2)])
            pygame.draw.polygon(surf, (255, 240, 200), [(base[0] - 6, base[1]),
                                                        (base[0] + 6, base[1]),
                                                        (base[0], base[1] + fl)])
        pad = R.project_point((0, 0, 0), cam)
        if pad:
            for p in self.smoke:
                a = max(0, min(255, int(p[4] * 160)))
                r = int(10 + (1 - p[4]) * 40)
                c = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(c, (200, 196, 190, a // 2), (r, r), r)
                surf.blit(c, (pad[0] + p[0] - r, pad[1] + p[1] * 0.25 - r))
        if self.boom_at is not None:
            centre = R.project_point((0, h + top * 0.3, 0), cam) or (640, 360)
            age = self.t - self.boom_at
            if age < 0.5:
                ui.overlay(surf, (255, 160, 60), 200 * (1 - age / 0.5))
            pygame.draw.circle(surf, D.ORANGE, centre, int(30 + age * 220), 4)
            for p in self.debris:
                col = D.GOLD if p[4] > 1.0 else D.ORANGE
                pygame.draw.circle(surf, col, (int(centre[0] + p[0]), int(centre[1] + p[1])), 3)
        # HUD
        if self.t < COUNT:
            n = 3 - int(self.t / (COUNT / 3))
            ui.text(surf, "T-%d" % n, (640, 140), 96, D.CREAM, "title", anchor="center")
        elif self.boom_at is None:
            ui.text(surf, "LIFTOFF" if lift < STAGE else ("STAGE SEPARATION"
                                                          if lift < STAGE + 1.4 else "ON COURSE"),
                    (640, 90), 34, D.GOLD, "title", anchor="center")
        else:
            ui.text(surf, "TOO HEAVY" if self.heavy else "LAUNCH FAILURE", (640, 90), 40,
                    D.RED, "title", anchor="center")
            ui.text_box(surf, self.s["result"]["phases"][0]["message"], (390, 600, 500, 80), 15,
                        D.CREAM)
        ui.text(surf, "ALT %6.1f km" % (max(0, h) * 12), (40, 40), 16, D.HUD, "bold")
        ui.text(surf, "SEED %d" % self.s["seed"], (40, 64), 12, D.DIM)
        ui.text(surf, "click to skip", (1240, 690), 12, D.DIM, anchor="bottomright")
