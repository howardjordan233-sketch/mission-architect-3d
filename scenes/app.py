"""App state and scene switching, shared by main.py and the test harness."""
import importlib
import random

from game import data as D
from game import team
from scenes import ui

SCENES = {
    "title": ("scenes.title", "TitleScene"),
    "hangar": ("scenes.hangar", "HangarScene"),
    "gonogo": ("scenes.gonogo", "GoNoGoScene"),
    "launch": ("scenes.launch", "LaunchScene"),
    "flight": ("scenes.flight", "FlightScene"),
    "debrief": ("scenes.debrief", "DebriefScene"),
}
DEMO_SEED = 10  # Mars rover: a dust storm hits the solar design on this seed
# goal cards for the demo: they reward planning for the dust storm
DEMO_CARDS = {"director": "no_damage", "engineer": "mass_margin", "science": "top_instr",
              "comms": "data_90"}


def demo_cards():
    return {role: next(c for c in D.GOAL_CARDS[role] if c["id"] == cid)
            for role, cid in DEMO_CARDS.items()}


class App:
    def __init__(self, screen):
        self.screen = screen
        self.stars = ui.Starfield()
        self.running = True
        self.scene = None
        self.s = {
            "difficulty": "engineer",
            "mission": "mars",
            "orbit": "mars_rover",
            "player_count": 1,
            "names": ["", "", "", ""],
            "players": team.deal_roles(1),
            "cards": team.deal_goal_cards(),
            "turn": 0,
            "design": D.empty_design("mars", "mars_rover"),
            "seed": 0,
            "fixed_seed": None,
            "result": None,
            "score": None,
            "code": "",
            "attempt": 0,
            "history": [],
        }
        self.go("title")

    def go(self, name, **kw):
        mod, cls = SCENES[name]
        self.scene = getattr(importlib.import_module(mod), cls)(self, **kw)

    def new_mission(self):
        """Fresh design, roles and goal cards from the title choices."""
        s = self.s
        s["players"] = team.deal_roles(s["player_count"], s["names"])
        if s["fixed_seed"] == DEMO_SEED:
            s["cards"] = demo_cards()
        else:
            s["cards"] = team.deal_goal_cards(random.randrange(10 ** 6))
        s["design"] = D.empty_design(s["mission"], s["orbit"], s["difficulty"])
        s["turn"] = 0
        s["attempt"] = 0
        s["history"] = []

    def toggle_demo(self):
        """F9: a fixed seed and fixed goal cards, so the pitch demo is identical every time."""
        s = self.s
        s["fixed_seed"] = None if s["fixed_seed"] is not None else DEMO_SEED
        if s["fixed_seed"] is not None:
            s["cards"] = demo_cards()
        return s["fixed_seed"]

    def team_name(self):
        names = [p["name"] for p in self.s["players"]]
        if len(names) == 1:
            return names[0] if names[0] != "Player 1" else "Mission Architect"
        short = [n.split(" ")[0] for n in names]
        return " & ".join(short) if len(short) == 2 else ", ".join(short)

    def goal_ids(self):
        return [c["id"] for c in self.s["cards"].values()]

    def roll_seed(self):
        s = self.s
        s["seed"] = s["fixed_seed"] if s["fixed_seed"] is not None else random.randrange(256)
        return s["seed"]
