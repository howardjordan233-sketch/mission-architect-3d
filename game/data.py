"""Mission Architect 3D game catalog.

Pure data, no pygame. Numbers are simplified game values based on public
NASA and launch-provider figures (see README for sources).
Money is in millions of US dollars, mass in kg, power in watts.
"""

# ---------------------------------------------------------------- palette
CREAM = (238, 228, 206)
ORANGE = (214, 104, 41)
TEAL = (22, 96, 104)
SPACE = (12, 14, 20)
HUD = (120, 230, 140)
GOLD = (232, 186, 70)
STEEL = (150, 158, 168)
RED = (220, 70, 60)
YELLOW = (236, 200, 70)
PURPLE = (150, 90, 210)
DUST = (168, 110, 70)
WHITE = (245, 245, 240)
DIM = (90, 100, 110)

# ---------------------------------------------------------------- missions
MISSIONS = {
    "moon": {
        "name": "Moon: South Pole",
        "short": "MOON",
        "goal": "Find water ice in dark craters",
        "budget": 450,
        "sunlight": 1.00,
        "body_cost": 100,
        "body_mass": 600,
        "color": (200, 200, 205),
        "orbits": ["polar_orbiter", "south_lander"],
        "difficulty": "Easy",
    },
    "mars": {
        "name": "Mars: Water Hunter",
        "short": "MARS",
        "goal": "Find signs of ancient water",
        "budget": 900,
        "sunlight": 0.43,
        "body_cost": 200,
        "body_mass": 800,
        "color": (196, 90, 50),
        "orbits": ["mars_orbiter", "mars_rover"],
        "difficulty": "Medium",
    },
    "europa": {
        "name": "Europa: Ocean World",
        "short": "EUROPA",
        "goal": "Study the ice shell and hidden ocean",
        "budget": 1200,
        "sunlight": 0.04,
        "body_cost": 500,
        "body_mass": 2500,
        "color": (210, 190, 160),
        "orbits": ["europa_flybys", "europa_low"],
        "difficulty": "Hard",
    },
}
MISSION_ORDER = ["moon", "mars", "europa"]

# ---------------------------------------------------------------- orbits
ORBITS = {
    "polar_orbiter": {"name": "Polar orbiter", "landing": False, "drill_ok": False,
                      "science_x": 0.7, "radiation_x": 1.0, "lifetime": 3},
    "south_lander": {"name": "South Pole lander", "landing": True, "drill_ok": True,
                     "science_x": 1.0, "radiation_x": 1.0, "lifetime": 1},
    "mars_orbiter": {"name": "Orbiter", "landing": False, "drill_ok": False,
                     "science_x": 0.8, "radiation_x": 1.0, "lifetime": 4},
    "mars_rover": {"name": "Rover", "landing": True, "drill_ok": True,
                   "science_x": 1.0, "radiation_x": 1.0, "lifetime": 2},
    "europa_flybys": {"name": "Many flybys", "landing": False, "drill_ok": False,
                      "science_x": 1.0, "radiation_x": 0.5, "lifetime": 4},
    "europa_low": {"name": "Low orbit", "landing": False, "drill_ok": False,
                   "science_x": 1.15, "radiation_x": 2.0, "lifetime": 1},
}

# ---------------------------------------------------------------- parts
# Every part carries a 3D look: shape (cube, cylinder, cone), height,
# width (radius for round shapes, half-width for cubes) and color.

ROCKETS = {
    "small": {"name": "Small (Electron class)", "cost": 15, "rel": 0.95,
              "cap": {"moon": 50, "mars": 0, "europa": 0},
              "shape": "cylinder", "height": 3.0, "width": 0.30, "color": CREAM, "boosters": 0},
    "medium": {"name": "Medium (Falcon 9 class)", "cost": 70, "rel": 0.99,
               "cap": {"moon": 4000, "mars": 2500, "europa": 0},
               "shape": "cylinder", "height": 4.2, "width": 0.42, "color": CREAM, "boosters": 0},
    "heavy": {"name": "Heavy (Falcon Heavy class)", "cost": 150, "rel": 0.98,
              "cap": {"moon": 15000, "mars": 10000, "europa": 6500},
              "shape": "cylinder", "height": 4.6, "width": 0.46, "color": CREAM, "boosters": 2},
    "super": {"name": "Super heavy (SLS class)", "cost": 2000, "rel": 0.97,
              "cap": {"moon": 27000, "mars": 20000, "europa": 15000},
              "shape": "cylinder", "height": 5.6, "width": 0.6, "color": ORANGE, "boosters": 2},
}

# Giant arrays: 17,500 W x 4% sunlight = 700 W at Jupiter, matching NASA's
# "at least 700 watts" design figure for Europa Clipper's prime mission.
POWER = {
    "solar_s": {"name": "Small solar panels", "cost": 10, "mass": 50, "watts": 600,
                "solar": True, "shape": "cube", "height": 0.15, "width": 1.1, "color": TEAL},
    "solar_l": {"name": "Large solar panels", "cost": 30, "mass": 200, "watts": 2000,
                "solar": True, "shape": "cube", "height": 0.18, "width": 1.6, "color": TEAL},
    "solar_g": {"name": "Giant solar arrays", "cost": 80, "mass": 600, "watts": 17500,
                "solar": True, "shape": "cube", "height": 0.2, "width": 2.4, "color": TEAL},
    "rtg": {"name": "Nuclear power (RTG)", "cost": 150, "mass": 45, "watts": 300,
            "solar": False, "shape": "cylinder", "height": 0.7, "width": 0.25, "color": STEEL},
}

BATTERY = {"name": "Battery pack", "cost": 5, "mass": 30,
           "shape": "cube", "height": 0.25, "width": 0.3, "color": GOLD}

INSTRUMENTS = {
    "camera": {"name": "HD camera", "does": "Takes detailed pictures",
               "cost": 20, "mass": 15, "watts": 20, "data": 3,
               "pts": {"moon": 10, "mars": 10, "europa": 10},
               "shape": "cube", "height": 0.3, "width": 0.25, "color": (70, 76, 88)},
    "spectro": {"name": "Spectrometer", "does": "Reads what rocks and ice are made of",
                "cost": 40, "mass": 25, "watts": 30, "data": 2,
                "pts": {"moon": 15, "mars": 20, "europa": 15},
                "shape": "cylinder", "height": 0.35, "width": 0.2, "color": GOLD},
    "drill": {"name": "Drill", "does": "Grabs samples from below the surface",
              "cost": 60, "mass": 40, "watts": 80, "data": 1,
              "pts": {"moon": 20, "mars": 25, "europa": 0},
              "shape": "cone", "height": 0.5, "width": 0.2, "color": STEEL},
    "radar": {"name": "Ground or ice radar", "does": "Sees layers under the surface",
              "cost": 50, "mass": 30, "watts": 60, "data": 4,
              "pts": {"moon": 15, "mars": 15, "europa": 25},
              "shape": "cube", "height": 0.2, "width": 0.4, "color": ORANGE},
    "magneto": {"name": "Magnetometer", "does": "Detects hidden oceans by magnetic signals",
                "cost": 15, "mass": 5, "watts": 10, "data": 1,
                "pts": {"moon": 5, "mars": 5, "europa": 25},
                "shape": "cylinder", "height": 0.5, "width": 0.08, "color": CREAM},
    "thermal": {"name": "Thermal camera", "does": "Measures heat, finds warm spots",
                "cost": 25, "mass": 10, "watts": 15, "data": 2,
                "pts": {"moon": 10, "mars": 10, "europa": 15},
                "shape": "cube", "height": 0.25, "width": 0.22, "color": RED},
}
MAX_INSTRUMENTS = 4

COMMS = {
    "small_ant": {"name": "Small antenna", "cost": 5, "mass": 10, "watts": 20,
                  "reach": {"moon": 1.00, "mars": 0.60, "europa": 0.25},
                  "shape": "cone", "height": 0.4, "width": 0.15, "color": CREAM},
    "hga": {"name": "High-gain dish", "cost": 25, "mass": 40, "watts": 60,
            "reach": {"moon": 1.00, "mars": 1.00, "europa": 0.90},
            "shape": "cone", "height": 0.35, "width": 0.6, "color": CREAM},
    "relay": {"name": "Mars relay", "cost": 8, "mass": 5, "watts": 10,
              "reach": {"moon": 0.0, "mars": 0.95, "europa": 0.0},
              "shape": "cone", "height": 0.3, "width": 0.12, "color": HUD},
}
DOWNLINK_GB_PER_DAY = 10

PROTECTION = {
    "land_moon": {"name": "Landing system (Moon)", "cost": 60, "mass": 400,
                  "for": "moon", "shape": "cone", "height": 0.6, "width": 1.0, "color": STEEL},
    "land_mars": {"name": "Landing system (Mars)", "cost": 150, "mass": 1200,
                  "for": "mars", "shape": "cone", "height": 0.8, "width": 1.2, "color": ORANGE},
    "shield": {"name": "Radiation shielding", "cost": 40, "mass": 150,
               "for": None, "shape": "cube", "height": 0.5, "width": 0.75, "color": GOLD},
    "dust": {"name": "Dust covers and heaters", "cost": 10, "mass": 20,
             "for": None, "shape": "cube", "height": 0.12, "width": 0.7, "color": DUST},
}

BASE_WATTS = 100

# Parts shown in Cadet mode (three per category).
CADET_PARTS = {
    "rocket": ["small", "medium", "heavy"],
    "power": ["solar_l", "solar_g", "rtg"],
    "instruments": ["camera", "spectro", "radar"],
    "comms": ["small_ant", "hga", "relay"],
    "protection": ["land_moon", "land_mars", "shield"],
}

CATEGORIES = ["rocket", "power", "instruments", "comms", "protection"]
CATEGORY_NAMES = {"rocket": "Rocket", "power": "Power", "instruments": "Instruments",
                  "comms": "Comms", "protection": "Protection"}

# ---------------------------------------------------------------- team mode
ROLES = ["director", "engineer", "science", "comms"]
ROLE_INFO = {
    "director": {"name": "Flight Director", "controls": ["orbit"], "color": ORANGE},
    "engineer": {"name": "Spacecraft Engineer", "controls": ["rocket", "power", "protection"],
                 "color": TEAL},
    "science": {"name": "Science Lead", "controls": ["instruments"], "color": GOLD},
    "comms": {"name": "Comms & Budget Officer", "controls": ["comms"], "color": HUD},
}

GOAL_CARDS = {
    "director": [
        {"id": "no_damage", "text": "No unprevented events this mission"},
        {"id": "risky_3star", "text": "Riskier orbit and still 3+ stars"},
    ],
    "engineer": [
        {"id": "mass_margin", "text": "Keep a 10%+ mass margin"},
        {"id": "power_surplus", "text": "Make 10%+ more power than you use"},
    ],
    "science": [
        {"id": "three_instr", "text": "Carry 3 or more instruments"},
        {"id": "top_instr", "text": "Carry the top science instrument"},
    ],
    "comms": [
        {"id": "budget_20", "text": "Finish with 20%+ of the budget left"},
        {"id": "data_90", "text": "Get 90%+ of the data home"},
    ],
}
GOAL_POINTS = 5

# The riskier orbit of each mission (for the director's card).
RISKY_ORBIT = {"moon": "south_lander", "mars": "mars_rover", "europa": "europa_low"}

# ---------------------------------------------------------------- difficulty
DIFFICULTIES = {
    "cadet": {"name": "Cadet", "blurb": "Tips on, kinder luck",
              "event_x": 0.5, "budget": True, "events": True, "board": True},
    "engineer": {"name": "Engineer", "blurb": "Every part, full risk",
                 "event_x": 1.0, "budget": True, "events": True, "board": True},
    "sandbox": {"name": "Sandbox", "blurb": "No budget, no bad luck",
                "event_x": 0.0, "budget": False, "events": False, "board": False},
}
DIFFICULTY_ORDER = ["cadet", "engineer", "sandbox"]

# ---------------------------------------------------------------- score
SCORE_SPLIT = {"science": 50, "budget": 15, "reliability": 15, "goals": 20}
STARS = [(90, 5), (75, 4), (60, 3), (40, 2), (0, 1)]

# ---------------------------------------------------------------- NASA ghost
# Simplified: real missions mapped onto the closest game parts.
NASA = {
    "moon": {
        "mission": "Intuitive Machines IM-1 'Odysseus'",
        "when": "Landed Feb 2024",
        "orbit": "south_lander",
        "design": {"rocket": "medium", "power": "solar_s", "battery": False,
                   "instruments": ["camera"], "comms": "small_ant",
                   "protection": ["land_moon"]},
        "power": "Solar", "rocket": "Falcon 9",
        "lesson": "Landings are risky: it landed but tipped onto its side.",
    },
    "mars": {
        "mission": "Perseverance rover",
        "when": "Landed Feb 2021",
        "orbit": "mars_rover",
        "design": {"rocket": "medium", "power": "rtg", "battery": True,
                   "instruments": ["camera", "spectro", "drill", "radar"], "comms": "relay",
                   "protection": ["land_mars"]},
        "power": "Nuclear RTG", "rocket": "Atlas V",
        "lesson": "Nuclear power means dust storms don't matter.",
    },
    "europa": {
        "mission": "Europa Clipper",
        "when": "Launched Oct 2024, arrives 2030",
        "orbit": "europa_flybys",
        "design": {"rocket": "heavy", "power": "solar_g", "battery": False,
                   "instruments": ["radar", "magneto", "spectro", "thermal"], "comms": "hga",
                   "protection": ["shield"]},
        "power": "Giant solar arrays", "rocket": "Falcon Heavy",
        "lesson": "Huge solar arrays work even near Jupiter, and a radiation vault guards the electronics.",
    },
}

# ---------------------------------------------------------------- tips
TIPS = {
    "power": "Solar panels get weaker the farther you go: 43% at Mars, 4% at Jupiter.",
    "comms": "Science stuck on the spacecraft is worth nothing. A bigger antenna sends more home.",
    "mass": "Every kilogram has to fit on the rocket. Heavy parts can force a bigger, pricier rocket.",
    "shield": "Jupiter's radiation and solar flares fry unshielded electronics.",
    "dust": "Mars dust storms smother solar panels. Nuclear power doesn't care.",
    "night": "A lunar night lasts about two weeks. Batteries or nuclear power keep you alive.",
    "budget": "Leaving 25% of the budget unspent earns full budget points.",
}


DEST = {"moon": "the Moon", "mars": "Mars", "europa": "Europa"}


def empty_design(mission="mars", orbit=None, difficulty="engineer"):
    """A blank design for a mission."""
    if orbit is None:
        orbit = MISSIONS[mission]["orbits"][0]
    return {
        "mission": mission,
        "orbit": orbit,
        "difficulty": difficulty,
        "rocket": None,
        "power": None,
        "battery": False,
        "instruments": [],
        "comms": None,
        "protection": [],
    }


def parts_for(category, difficulty="engineer"):
    """Ids of the parts shown in a category for a difficulty."""
    table = {"rocket": ROCKETS, "power": POWER, "instruments": INSTRUMENTS,
             "comms": COMMS, "protection": PROTECTION}[category]
    ids = list(table.keys())
    if difficulty == "cadet":
        ids = [i for i in ids if i in CADET_PARTS[category]]
    return ids


def part_info(category, pid):
    """Look up any part by category and id."""
    if category == "battery":
        return BATTERY
    table = {"rocket": ROCKETS, "power": POWER, "instruments": INSTRUMENTS,
             "comms": COMMS, "protection": PROTECTION}[category]
    return table[pid]
