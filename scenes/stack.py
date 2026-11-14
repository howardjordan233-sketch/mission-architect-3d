"""Turns a design into a list of 3D parts for game.render3d.

Layout only: every number about the game itself comes from game/.
Returns (parts, top_y) where top_y is the height of the whole stack.
"""
import math

from game import data as D


def panel_color(sunlight):
    """The sunlight dimmer: solar panels glow less far from the Sun."""
    g = 0.25 + 0.75 * math.sqrt(sunlight)
    return (int(20 + 50 * g), int(60 + 150 * g), int(70 + 150 * g))


def build(design, rocket_on=True, ghost=False, x=0.0, z=0.0, spin=0.0):
    parts = []
    m = D.MISSIONS[design["mission"]]
    big = 1.25 if design["mission"] == "europa" else 1.0
    y = 0.0

    def add(**p):
        p["x"] = p.get("x", 0.0) + x
        p["z"] = p.get("z", 0.0) + z
        if spin:
            # rotate the part's position around the stack's own axis
            px, pz = p["x"] - x, p["z"] - z
            c, s = math.cos(spin), math.sin(spin)
            p["x"], p["z"] = x + px * c + pz * s, z - px * s + pz * c
            p["yaw"] = p.get("yaw", 0.0) + spin
        if ghost:
            p["alpha"] = 38
            p["edge"] = D.HUD
        parts.append(p)

    # ---- launch vehicle
    if rocket_on and design["rocket"]:
        r = D.ROCKETS[design["rocket"]]
        rw, rh = r["width"], r["height"]
        add(shape="cylinder", height=rh, width=rw, y=y, color=r["color"],
            sides=12, smooth=True, tag="rocket")
        add(shape="cylinder", height=0.16, width=rw * 1.03, y=y + rh * 0.66,
            color=D.SPACE, sides=12, smooth=True, tag="rocket")
        add(shape="cylinder", height=0.12, width=rw * 1.03, y=y + 0.3,
            color=D.ORANGE, sides=12, smooth=True, tag="rocket")
        for k in range(r.get("boosters", 0)):
            side = -1 if k == 0 else 1
            bw = rw * 0.62
            add(shape="cylinder", height=rh * 0.72, width=bw, x=side * (rw + bw + 0.02), y=y,
                color=D.CREAM if r["color"] != D.CREAM else (225, 220, 205), sides=10,
                smooth=True, tag="rocket")
            add(shape="cone", height=bw * 2.2, width=bw, x=side * (rw + bw + 0.02),
                y=y + rh * 0.72, color=D.CREAM, sides=10, smooth=True, tag="rocket")
        for k in range(4):  # fins
            a = k * math.pi / 2 + math.pi / 4
            add(shape="cube", height=0.55, width=0.04, sx=0.04, sz=0.22,
                x=math.cos(a) * (rw + 0.18), z=math.sin(a) * (rw + 0.18), y=y,
                yaw=-a, color=D.ORANGE, tag="rocket")
        y += rh
        add(shape="cylinder", height=0.14, width=rw * 0.85, y=y, color=D.STEEL,
            sides=12, smooth=True, tag="adapter")
        y += 0.14

    # ---- landing system (legs + engine skirt)
    land = [p for p in design["protection"] if p.startswith("land_")]
    if land:
        lp = D.PROTECTION[land[0]]
        legs_h = lp["height"]
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            add(shape="cube", height=legs_h, width=0.05, sx=0.05, sz=0.05,
                x=math.cos(a) * 0.62 * big, z=math.sin(a) * 0.62 * big, y=y,
                yaw=-a, tilt=0.35, color=lp["color"], tag="legs")
        add(shape="cone", height=legs_h * 0.7, width=0.35 * big, y=y, color=D.STEEL,
            sides=8, smooth=True, tag="engine")
        y += legs_h * 0.75

    body_y, body_h, body_w = y, 0.9 * big, 0.55 * big

    # ---- radiation vault (around the body)
    if "shield" in design["protection"]:
        add(shape="cube", height=body_h * 0.7, width=body_w * 1.18, y=y + body_h * 0.15,
            color=D.GOLD, tag="shield")

    # ---- body
    add(shape="cube", height=body_h, width=body_w, y=y, color=D.CREAM, tag="body")
    add(shape="cube", height=0.06, width=body_w * 1.03, y=y + body_h * 0.55,
        color=D.ORANGE, tag="body")
    y += body_h

    # ---- power
    if design["power"]:
        p = D.POWER[design["power"]]
        mid = body_y + body_h * 0.55
        if p["solar"]:
            col = panel_color(m["sunlight"])
            span = p["width"] * big
            for side in (-1, 1):
                add(shape="cube", height=0.04, width=span / 2, sx=span / 2, sz=0.32 * big,
                    x=side * (body_w + span / 2 + 0.06), y=mid, color=col,
                    glow=(120, 255, 240) if m["sunlight"] > 0.5 else None, tag="power")
                add(shape="cube", height=0.03, width=0.06, sx=0.06, sz=0.03,
                    x=side * (body_w + 0.03), y=mid, color=D.STEEL, tag="power")
        else:
            add(shape="cylinder", height=p["height"], width=p["width"], x=-body_w - 0.28,
                y=body_y + 0.05, tilt=-0.5, color=p["color"], sides=8, tag="power")
            add(shape="cube", height=p["height"] * 0.8, width=0.05, sx=0.3, sz=0.02,
                x=-body_w - 0.28, y=body_y + 0.1, tilt=-0.5, color=D.DIM, tag="power")
    if design["battery"]:
        add(shape="cube", height=0.25, width=0.18, x=body_w + 0.18, y=body_y + 0.08,
            color=D.GOLD, tag="battery")

    # ---- dust covers
    if "dust" in design["protection"]:
        add(shape="cube", height=0.05, width=body_w * 1.08, y=y, color=D.DUST, tag="dust")
        y += 0.05

    # ---- instruments on the top deck
    n = len(design["instruments"])
    for i, iid in enumerate(design["instruments"]):
        inst = D.INSTRUMENTS[iid]
        a = (i / max(1, n)) * 2 * math.pi + 0.4
        rr = body_w * 0.55 if n > 1 else 0.0
        h = inst["height"]
        if iid == "drill":  # drill points down under the body
            add(shape="cylinder", height=0.5, width=0.06, x=body_w * 0.6, z=0.0,
                y=body_y - 0.45, color=D.STEEL, sides=6, tag="instrument")
            add(shape="cone", height=0.18, width=0.1, x=body_w * 0.6, y=body_y - 0.62,
                color=D.STEEL, sides=6, tag="instrument")
            continue
        add(shape=inst["shape"], height=h * 1.15, width=inst["width"] * 0.9,
            x=math.cos(a) * rr, z=math.sin(a) * rr, y=y, color=inst["color"],
            sides=8, tag="instrument")

    # ---- comms on a short mast
    top = y + 0.35
    if design["comms"]:
        c = D.COMMS[design["comms"]]
        add(shape="cylinder", height=0.35, width=0.04, y=y, color=D.STEEL, sides=6, tag="comms")
        if design["comms"] == "hga":
            add(shape="cone", height=0.22, width=0.55 * big, y=y + 0.35, color=c["color"],
                sides=12, tag="comms")
            add(shape="cylinder", height=0.25, width=0.03, y=y + 0.45, color=D.STEEL,
                sides=6, tag="comms")
            top = y + 0.75
        else:
            add(shape="cone", height=c["height"], width=c["width"], y=y + 0.35,
                color=c["color"], sides=8, tag="comms")
            top = y + 0.35 + c["height"]
    return parts, max(top, y)
