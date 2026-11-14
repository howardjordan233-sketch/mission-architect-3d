"""The hangar: build the spacecraft part by part in 3D, watch six meters react."""
import pygame

from game import data as D
from game import engine as E
from game import render3d as R
from game import team
from scenes import stack, ui
from scenes.base import Scene

VIEW = pygame.Rect(350, 64, 584, 600)
TAB_LABEL = {"rocket": "ROCKET", "power": "POWER", "instruments": "SCIENCE",
             "comms": "COMMS", "protection": "PROTECT"}


def part_sub(cat, pid, design):
    """Short spec line under a part button."""
    m = design["mission"]
    if cat == "rocket":
        r = D.ROCKETS[pid]
        cap = r["cap"][m]
        return "$%dM  %s  %d%%" % (r["cost"], ("%d kg lift" % cap) if cap else "can't reach",
                                   r["rel"] * 100)
    if cat == "power":
        p = D.POWER[pid]
        here = round(p["watts"] * D.MISSIONS[m]["sunlight"]) if p["solar"] else p["watts"]
        return "$%dM  %dkg  %d W here" % (p["cost"], p["mass"], here)
    if cat == "instruments":
        i = D.INSTRUMENTS[pid]
        return "$%dM %dkg %dW  %d pts" % (i["cost"], i["mass"], i["watts"], i["pts"][m])
    if cat == "comms":
        c = D.COMMS[pid]
        return "$%dM %dkg %dW  %d%% reach" % (c["cost"], c["mass"], c["watts"],
                                              c["reach"][m] * 100)
    p = D.PROTECTION[pid]
    return "$%dM  %d kg" % (p["cost"], p["mass"])


def part_help(cat, pid):
    if cat == "instruments":
        return D.INSTRUMENTS[pid]["does"] + "."
    if cat == "rocket":
        return "Lifts your spacecraft. Bigger rockets carry more but cost more. % is reliability."
    if cat == "power":
        if pid == "rtg":
            return "Nuclear power: same watts everywhere, ignores dust and darkness. Pricey."
        return "Solar panels: free power, but weaker the farther you are from the Sun."
    if cat == "comms":
        return "Sends data home. Science that never reaches Earth earns nothing."
    return {"land_moon": "Thrusters and legs. Required to land on the Moon.",
            "land_mars": "Heat shield, parachute and sky crane. Required to land on Mars.",
            "shield": "A radiation vault. Blocks solar flares and Jupiter's radiation.",
            "dust": "Keeps dust off panels and adds heaters for freezing nights."}[pid]


class HangarScene(Scene):
    def __init__(self, app, note=None):
        super().__init__(app)
        self.cat = "rocket"
        self.yaw, self.pitch, self.zoom = 0.6, 0.25, 1.0
        self.drag = None
        self.idle = 0.0
        self.peek = False
        self.hover_help = ""
        self.pop = {}  # part tag -> time added, for a little bounce
        if note:
            self.say(note, D.GOLD, 4)
        self.build()

    # ---------------------------------------------------------------- state
    @property
    def d(self):
        return self.s["design"]

    def solo(self):
        return len(self.s["players"]) == 1

    def player(self):
        return self.s["players"][self.s["turn"]]

    def can_edit(self, cat):
        return self.solo() or cat in team.controls(self.player())

    def owner_name(self, cat):
        i = team.owner_of(cat, self.s["players"])
        for r in self.s["players"][i]["roles"]:
            if cat in D.ROLE_INFO[r]["controls"]:
                return D.ROLE_INFO[r]["name"]
        return ""

    # ---------------------------------------------------------------- buttons
    def build(self):
        d = self.d
        diff = d["difficulty"]
        b = []
        # category tabs
        for i, cat in enumerate(D.CATEGORIES):
            b.append(ui.Button((16 + i * 65, 64, 62, 30), TAB_LABEL[cat],
                               on=lambda c=cat: self.set_cat(c), selected=self.cat == cat,
                               size=11, accent=D.TEAL if self.can_edit(cat) else D.DIM))
        editable = self.can_edit(self.cat)
        y = 104
        for pid in D.parts_for(self.cat, diff):
            info = D.part_info(self.cat, pid)
            sel = self.is_on(self.cat, pid)
            ok = editable
            if self.cat == "protection" and D.PROTECTION[pid]["for"] not in (None, d["mission"]):
                ok = False
            b.append(ui.Button((16, y, 318, 50), info["name"], on=lambda p=pid: self.toggle(p),
                               enabled=ok, selected=sel, sub=part_sub(self.cat, pid, d),
                               size=14))
            b[-1].help = part_help(self.cat, pid)
            y += 56
        if self.cat == "power":
            b.append(ui.Button((16, y + 4, 318, 40), "+ Battery pack  ($5M, 30 kg)",
                               on=self.toggle_battery, enabled=editable,
                               selected=d["battery"], size=13))
            b[-1].help = "Stores power to survive one dark spell, like a two-week lunar night."
        # orbit (flight director)
        for i, oid in enumerate(D.MISSIONS[d["mission"]]["orbits"]):
            b.append(ui.Button((420 + i * 150, 12, 144, 36), D.ORBITS[oid]["name"],
                               on=lambda o=oid: self.set_orbit(o), selected=d["orbit"] == oid,
                               enabled=self.can_edit("orbit"), size=12))
        # right column
        b.append(ui.Button((950, 612, 314, 52), "LAUNCH  >", on=self.launch,
                           enabled=E.can_launch(d), selected=E.can_launch(d), size=20))
        if not self.solo():
            nxt = self.s["players"][(self.s["turn"] + 1) % len(self.s["players"])]["name"]
            b.append(ui.Button((950, 556, 154, 46), "PASS TO", on=self.pass_turn,
                               sub=nxt[:14], size=13))
        b.append(ui.Button((1110 if not self.solo() else 950, 556,
                            154 if not self.solo() else 314, 46),
                           "GOAL CARD (G)", on=None, size=12, accent=D.GOLD))
        self.peek_btn = b[-1]
        b.append(ui.Button((1186, 12, 80, 36), "MENU", on=lambda: self.app.go("title"), size=12))
        self.buttons = b

    def is_on(self, cat, pid):
        d = self.d
        if cat in ("instruments", "protection"):
            return pid in d[cat]
        return d[cat] == pid

    def set_cat(self, cat):
        self.cat = cat
        self.build()

    def set_orbit(self, oid):
        self.d["orbit"] = oid
        self.s["orbit"] = oid
        self.build()

    def toggle(self, pid):
        d, cat = self.d, self.cat
        if cat == "instruments":
            if pid in d["instruments"]:
                d["instruments"].remove(pid)
            elif len(d["instruments"]) >= D.MAX_INSTRUMENTS:
                self.say("Four instruments max. Remove one first.", D.YELLOW)
                return
            else:
                d["instruments"].append(pid)
        elif cat == "protection":
            if pid in d["protection"]:
                d["protection"].remove(pid)
            else:
                d["protection"].append(pid)
        else:
            d[cat] = None if d[cat] == pid else pid
        self.pop[cat] = self.t
        self.build()

    def toggle_battery(self):
        self.d["battery"] = not self.d["battery"]
        self.build()

    def pass_turn(self):
        self.s["turn"] = (self.s["turn"] + 1) % len(self.s["players"])
        p = self.player()
        # jump to the first tab this player controls
        for cat in D.CATEGORIES:
            if cat in team.controls(p):
                self.cat = cat
                break
        self.say("%s's turn: %s" % (p["name"], ", ".join(D.ROLE_INFO[r]["name"]
                                                         for r in p["roles"])), D.GOLD)
        self.build()

    def launch(self):
        if E.can_launch(self.d):
            self.app.go("gonogo")

    # ---------------------------------------------------------------- input
    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_g:
            self.peek = True
        elif e.type == pygame.KEYUP and e.key == pygame.K_g:
            self.peek = False
        elif e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.launch()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.peek_btn.rect.collidepoint(e.pos):
                self.peek = True
            elif VIEW.collidepoint(e.pos):
                self.drag = (e.pos, self.yaw, self.pitch)
            else:
                super().handle(e)
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.drag = None
            self.peek = False
        elif e.type == pygame.MOUSEMOTION and self.drag:
            (sx, sy), y0, p0 = self.drag
            self.yaw = y0 + (e.pos[0] - sx) * 0.01
            self.pitch = max(-0.1, min(1.2, p0 + (e.pos[1] - sy) * 0.006))
            self.idle = 0
        elif e.type == pygame.MOUSEWHEEL:
            self.zoom = max(0.45, min(1.8, self.zoom - e.y * 0.08))

    def update(self, dt):
        super().update(dt)
        self.idle += dt
        if not self.drag and self.idle > 2.5:
            self.yaw += dt * 0.25
        self.hover_help = ""
        m = self.mouse()
        for b in self.buttons:
            if getattr(b, "help", None) and b.rect.collidepoint(m):
                self.hover_help = b.help

    # ---------------------------------------------------------------- draw
    def draw(self, surf):
        d = self.d
        m = D.MISSIONS[d["mission"]]
        self.app.stars.draw(surf, self.t, 1.5)

        # 3D view
        parts, top = stack.build(d)
        sub = surf.subsurface(VIEW)
        cam = R.make_camera(VIEW.w, VIEW.h, yaw=self.yaw, pitch=self.pitch,
                            dist=(top * 1.0 + 2.6) * self.zoom, target=(0, top * 0.58, 0))
        ui.grid_floor(sub, cam, size=5)
        # launch pad
        pad = [{"shape": "cylinder", "height": 0.12, "width": 1.6, "y": -0.12,
                "color": (60, 66, 74), "sides": 16, "smooth": True}]
        ui.draw_faces(sub, R.render(pad + parts, cam))
        ui.text(sub, "SUNLIGHT AT %s: %d%%" % (m["short"], m["sunlight"] * 100), (12, 10), 13,
                stack.panel_color(m["sunlight"]), "bold")
        ui.text(sub, "drag to orbit / scroll to zoom", (VIEW.w - 12, 12), 11, D.DIM,
                anchor="topright")
        if not d["rocket"]:
            ui.text(sub, "Start with a rocket", (VIEW.w // 2, VIEW.h // 2 + 120), 18, D.CREAM,
                    "title", anchor="center")
        pygame.draw.rect(surf, ui.EDGE, VIEW, 1, border_radius=8)

        # top bar
        ui.text(surf, m["name"].upper(), (16, 14), 20, D.CREAM, "title")
        ui.text(surf, m["goal"], (18, 42), 12, D.HUD)
        ui.text(surf, "ORBIT", (372, 30), 11, D.DIM, "bold", anchor="center")
        diff = D.DIFFICULTIES[d["difficulty"]]["name"].upper()
        ui.text(surf, diff + ("  / DEMO SEED" if self.s["fixed_seed"] is not None else ""),
                (1090, 30), 12, D.GOLD, "bold", anchor="midright")
        if not self.solo():
            p = self.player()
            roles = ", ".join(D.ROLE_INFO[r]["name"] for r in p["roles"])
            col = D.ROLE_INFO[p["roles"][0]]["color"]
            band = pygame.Rect(VIEW.x + 1, VIEW.bottom - 44, VIEW.w - 2, 43)
            pygame.draw.rect(surf, ui.mix(col, ui.PANEL, 0.75), band,
                             border_bottom_left_radius=8, border_bottom_right_radius=8)
            ui.text(surf, "%s'S TURN" % p["name"].upper(), (band.x + 14, band.centery), 15, col,
                    "bold", anchor="midleft")
            ui.text(surf, roles, (band.right - 14, band.centery), 12, D.CREAM,
                    anchor="midright")

        # left panel
        ui.panel(surf, (8, 56, 334, 608))
        if not self.can_edit(self.cat):
            ui.text(surf, "LOCKED: %s's controls" % self.owner_name(self.cat), (175, 650), 12,
                    D.YELLOW, "bold", anchor="center")
        tip = self.hover_help or self.cadet_tip()
        if tip:
            ui.text_box(surf, tip, (20, 566, 310, 70), 12, D.CREAM)

        # right panel: meters + checklist
        ui.panel(surf, (942, 56, 330, 492), "MISSION CONTROL")
        y = 94
        for label, value, frac, st in E.meters(d):
            ui.meter(surf, (958, y, 298, 30), label, value, frac, st)
            y += 42
        y += 4
        ui.text(surf, "PRE-LAUNCH CHECK", (958, y), 12, D.DIM, "bold")
        y += 20
        for item in E.launch_check(d)[:8]:
            col = D.HUD if item["ok"] else (D.RED if item["blocking"] else D.YELLOW)
            ui.text(surf, "OK" if item["ok"] else "!!", (958, y), 12, col, "bold")
            ui.text(surf, item["item"], (986, y), 12, D.CREAM if item["ok"] else col)
            y += 18

        self.draw_buttons(surf)
        if self.peek:
            self.draw_peek(surf)
        self.draw_toast(surf)

    def cadet_tip(self):
        d = self.d
        if d["difficulty"] != "cadet":
            return ""
        for item in E.launch_check(d):
            if not item["ok"]:
                return "TIP: " + item["why"]
        made, used = E.power_made(d), E.power_used(d)
        if made < used * 1.1:
            return "TIP: " + D.TIPS["power"]
        o = D.ORBITS[d["orbit"]]
        if d["mission"] == "europa" and "shield" not in d["protection"]:
            return "TIP: " + D.TIPS["shield"] + " Without it the mission lasts half as long."
        if d["mission"] == "mars" and o["landing"] and d["power"] != "rtg" \
                and "dust" not in d["protection"]:
            return "TIP: " + D.TIPS["dust"]
        if d["mission"] == "moon" and o["landing"] and d["power"] != "rtg" \
                and not d["battery"] and "dust" not in d["protection"]:
            return "TIP: " + D.TIPS["night"]
        if E.data_returned_frac(d) < 0.9:
            return "TIP: " + D.TIPS["comms"]
        return "TIP: Looks ready. Leaving 25% of the budget earns full budget points."

    def draw_peek(self, surf):
        roles = self.player()["roles"] if not self.solo() else D.ROLES
        h = 70 + 64 * len(roles)
        r = pygame.Rect(0, 0, 560, h)
        r.center = (640, 360)
        ui.overlay(surf, (0, 0, 0), 150)
        ui.panel(surf, r, "SECRET GOAL CARD%s  (+%d each)" % ("S" if len(roles) > 1 else "",
                                                             D.GOAL_POINTS), D.GOLD)
        y = r.y + 44
        for role in roles:
            card = self.s["cards"][role]
            ui.text(surf, D.ROLE_INFO[role]["name"].upper(), (r.x + 20, y), 12,
                    D.ROLE_INFO[role]["color"], "bold")
            ui.text(surf, card["text"], (r.x + 20, y + 20), 16, D.CREAM, "title")
            y += 64
        ui.text(surf, "Let go to hide it", (r.centerx, r.bottom - 18), 11, D.DIM,
                anchor="center")
