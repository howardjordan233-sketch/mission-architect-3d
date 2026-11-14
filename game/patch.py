"""The mission patch as pure data. scenes/patch_draw.py draws it."""
from game import data as D

RING = {"moon": D.STEEL, "mars": D.ORANGE, "europa": D.TEAL}
FIELD = {"moon": (28, 32, 48), "mars": (46, 24, 20), "europa": (14, 34, 44)}
POWER_ICON = {"solar_s": "panel", "solar_l": "panel", "solar_g": "panel", "rtg": "atom"}
INSTR_ICON = {"camera": "lens", "spectro": "prism", "drill": "drill", "radar": "waves",
              "magneto": "loop", "thermal": "flame"}


def patch_design(design, score_result, team_name="MISSION ARCHITECT"):
    m = design["mission"]
    return {
        "ring": RING[m],
        "field": FIELD[m],
        "planet": D.MISSIONS[m]["color"],
        "top_text": team_name.upper()[:20],
        "bottom_text": D.MISSIONS[m]["short"] + " / " + D.ORBITS[design["orbit"]]["name"].upper(),
        "icons": [POWER_ICON.get(design["power"] or "", "panel")]
                 + [INSTR_ICON[i] for i in design["instruments"]],
        "stars": score_result.get("stars", 1),
        "score": score_result.get("total", 0),
        "lander": D.ORBITS[design["orbit"]]["landing"],
    }
