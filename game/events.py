"""The dice: plays the four mission phases and rolls surprise events.

Each phase returns an "effect" word the 3D scenes react to:
failure, flare, radiation, rough_landing, dust, night, discovery, none.
"""
import random

from game import data as D
from game import engine as E

PHASES = ["Launch", "Cruise", "Arrival", "Science"]


def _phase(name, event, prevented, message, effect, bad=True, lost=None):
    return {"phase": name, "event": event, "prevented": prevented,
            "message": message, "effect": effect, "bad": bad, "lost": list(lost or [])}


def rocket_class(rocket):
    """'Medium (Falcon 9 class)' -> 'Falcon 9 class'."""
    name = rocket["name"]
    return name[name.find("(") + 1:name.rfind(")")] if "(" in name else name


def _lose(rng, alive, n):
    """Removes n random instruments from alive. Returns their ids."""
    lost = []
    for _ in range(min(n, len(alive))):
        pick = rng.choice(alive)
        alive.remove(pick)
        lost.append(pick)
    return lost


def _names(ids):
    return [D.INSTRUMENTS[i]["name"] for i in ids]


def run_mission(design, seed=None):
    rng = random.Random(seed)
    mission = design["mission"]
    orbit = E.orbit_of(design)
    diff = D.DIFFICULTIES[design["difficulty"]]
    odds = diff["event_x"]
    events_on = diff["events"]
    has = set(design["protection"])
    # canonical order, so a challenge code replays the exact same luck
    order = list(D.INSTRUMENTS)
    alive = sorted(design["instruments"], key=order.index)
    phases = []
    solar_x, science_x, bonus = 1.0, 1.0, 0
    unprevented = 0

    def result(lost=False, reason=None):
        sci = 0.0 if lost else E.science_collected(design, alive, solar_x, science_x, bonus)
        return {"phases": phases, "science": sci, "lost": lost, "lost_reason": reason,
                "unprevented": unprevented, "alive": list(alive),
                "solar_x": solar_x, "science_x": science_x}

    # ---- Launch
    if not E.launch_succeeds_on_mass(design):
        phases.append(_phase("Launch", "Too heavy", False,
                             "The rocket strains, wobbles and falls back. %d kg is more than "
                             "it can lift to %s." % (E.total_mass(design), D.DEST[mission]),
                             "failure"))
        return result(True, "mass")
    rocket = D.ROCKETS[design["rocket"]]
    fail_chance = (1 - rocket["rel"]) * odds
    if events_on and rng.random() < fail_chance:
        unprevented += 1
        phases.append(_phase("Launch", "Rocket failure", False,
                             "A rare engine failure. %s rockets succeed %d%% of the time; "
                             "today was the other %d%%." % (rocket_class(rocket),
                                                            rocket["rel"] * 100,
                                                            round((1 - rocket["rel"]) * 100)),
                             "failure"))
        return result(True, "rocket")
    phases.append(_phase("Launch", "Clean launch", True,
                         "Liftoff! Your %s rocket puts you on course." % rocket_class(rocket),
                         "none", bad=False))

    # ---- Cruise: solar flare
    if events_on and rng.random() < 0.30 * odds:
        if "shield" in has:
            phases.append(_phase("Cruise", "Solar flare", True,
                                 "A solar flare hits. Your radiation shielding absorbs it.",
                                 "flare"))
        else:
            lost = _lose(rng, alive, 1)
            unprevented += 1
            phases.append(_phase("Cruise", "Solar flare", False,
                                 "A solar flare fries the %s. Radiation shielding would have "
                                 "saved it." % (_names(lost)[0] if lost else "spare electronics"),
                                 "flare", lost=lost))
    else:
        phases.append(_phase("Cruise", "Quiet cruise", True,
                             "The Sun stays calm during the long cruise.", "none", bad=False))

    # ---- Arrival
    if mission == "europa":
        n = max(1, min(3, round(2 * orbit["radiation_x"])))
        if not events_on:
            phases.append(_phase("Arrival", "Jupiter radiation belt", True,
                                 "Sandbox: radiation is switched off.", "radiation", bad=False))
        elif "shield" in has and n <= 2:
            phases.append(_phase("Arrival", "Jupiter radiation belt", True,
                                 "Jupiter's radiation belt rages, but the shielding vault "
                                 "keeps the electronics alive.", "radiation"))
        elif "shield" in has:
            lost = _lose(rng, alive, n - 2)
            phases.append(_phase("Arrival", "Jupiter radiation belt", True,
                                 "This low, the radiation is fierce. The vault saves most "
                                 "electronics, but the %s is lost." % " and ".join(_names(lost)),
                                 "radiation", lost=lost))
        else:
            lost = _lose(rng, alive, n)
            unprevented += 1
            phases.append(_phase("Arrival", "Jupiter radiation belt", False,
                                 "Jupiter's radiation destroys the %s. No shielding, and the "
                                 "mission will also last half as long."
                                 % (" and ".join(_names(lost)) if lost else "spare parts"),
                                 "radiation", lost=lost))
    elif orbit["landing"]:
        if events_on and rng.random() < 0.10 * odds:
            lost = _lose(rng, alive, 1)
            unprevented += 1
            phases.append(_phase("Arrival", "Rough landing", False,
                                 "A rough landing on uneven ground breaks the %s. "
                                 "Sometimes it's just luck." % (_names(lost)[0] if lost
                                                               else "a leg"),
                                 "rough_landing", lost=lost))
        else:
            phases.append(_phase("Arrival", "Touchdown", True,
                                 "The landing system sets you down gently.", "none", bad=False))
    else:
        phases.append(_phase("Arrival", "Orbit insertion", True,
                             "Engines fire and you slip into %s." % orbit["name"].lower(),
                             "none", bad=False))

    # ---- Science
    if events_on and mission == "mars" and orbit["landing"] and rng.random() < 0.40 * odds:
        if design["power"] == "rtg":
            phases.append(_phase("Science", "Dust storm", True,
                                 "A planet-wide dust storm blots out the Sun. Nuclear power "
                                 "doesn't care.", "dust"))
        elif "dust" in has:
            solar_x = 0.6
            phases.append(_phase("Science", "Dust storm", True,
                                 "A dust storm coats the panels. Dust covers keep the loss to "
                                 "40%.", "dust"))
        else:
            solar_x = 0.25
            unprevented += 1
            phases.append(_phase("Science", "Dust storm", False,
                                 "A dust storm smothers the solar panels: power drops 75%. "
                                 "Nuclear power or dust covers would have helped.", "dust"))
    elif events_on and mission == "moon" and orbit["landing"]:
        if design["power"] == "rtg" or design["battery"]:
            phases.append(_phase("Science", "Lunar night", True,
                                 "Two weeks of freezing darkness. The %s keeps you warm."
                                 % ("RTG" if design["power"] == "rtg" else "battery pack"),
                                 "night"))
        elif "dust" in has:
            science_x = 0.875
            phases.append(_phase("Science", "Lunar night", True,
                                 "The lunar night freezes everything. Heaters save half the "
                                 "lost science.", "night"))
        else:
            science_x = 0.75
            unprevented += 1
            phases.append(_phase("Science", "Lunar night", False,
                                 "The lunar night freezes the lander: science drops 25%. "
                                 "A battery or nuclear power would have kept it alive.",
                                 "night"))
    if events_on and "spectro" in alive and rng.random() < 0.15:
        bonus = 10
        phases.append(_phase("Science", "Lucky discovery", True,
                             "The spectrometer spots something unexpected: +10 science!",
                             "discovery", bad=False))
    elif len(phases) < 4:
        phases.append(_phase("Science", "Science operations", True,
                             "%d instrument%s collecting data." % (len(alive),
                                                                   "" if len(alive) == 1 else "s"),
                             "none", bad=False))
    return result()
