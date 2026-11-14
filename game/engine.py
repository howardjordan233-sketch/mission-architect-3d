"""The brain: cost, mass, power, data, lifetime, launch check and score.

Pure Python. A design is a dict made by data.empty_design().
"""
from game import data as D


def mission_of(design):
    return D.MISSIONS[design["mission"]]


def orbit_of(design):
    return D.ORBITS[design["orbit"]]


def _parts(design):
    """Yield (category, info) for every chosen part."""
    if design["rocket"]:
        yield "rocket", D.ROCKETS[design["rocket"]]
    if design["power"]:
        yield "power", D.POWER[design["power"]]
    if design["battery"]:
        yield "battery", D.BATTERY
    for i in design["instruments"]:
        yield "instruments", D.INSTRUMENTS[i]
    if design["comms"]:
        yield "comms", D.COMMS[design["comms"]]
    for p in design["protection"]:
        yield "protection", D.PROTECTION[p]


# ---------------------------------------------------------------- totals
def total_cost(design):
    return mission_of(design)["body_cost"] + sum(p["cost"] for _, p in _parts(design))


def total_mass(design):
    """Spacecraft mass. The rocket itself does not count."""
    return mission_of(design)["body_mass"] + sum(
        p["mass"] for c, p in _parts(design) if c != "rocket")


def budget_of(design):
    return mission_of(design)["budget"]


def budget_left(design):
    return budget_of(design) - total_cost(design)


def rocket_capacity(design):
    if not design["rocket"]:
        return 0
    return D.ROCKETS[design["rocket"]]["cap"][design["mission"]]


def power_made(design, solar_x=1.0):
    """Watts made at the destination at the start of the mission."""
    if not design["power"]:
        return 0
    p = D.POWER[design["power"]]
    if p["solar"]:
        return round(p["watts"] * mission_of(design)["sunlight"] * solar_x)
    return p["watts"]


def power_used(design):
    w = D.BASE_WATTS
    w += sum(D.INSTRUMENTS[i]["watts"] for i in design["instruments"])
    if design["comms"]:
        w += D.COMMS[design["comms"]]["watts"]
    return w


def power_ratio(made, used):
    """Share of time instruments can run: 150 W made for 200 W used = 0.75."""
    if used <= 0:
        return 1.0
    return max(0.0, min(1.0, made / used))


def data_made(design, instruments=None):
    """Gb per day the instruments produce."""
    ids = design["instruments"] if instruments is None else instruments
    return sum(D.INSTRUMENTS[i]["data"] for i in ids)


def downlink(design):
    """Gb per day that can reach Earth."""
    if not design["comms"]:
        return 0.0
    return D.DOWNLINK_GB_PER_DAY * D.COMMS[design["comms"]]["reach"][design["mission"]]


def data_returned_frac(design, instruments=None):
    made = data_made(design, instruments)
    if made <= 0:
        return 0.0 if not design["comms"] else 1.0
    return max(0.0, min(1.0, downlink(design) / made))


def lifetime_years(design):
    """Years the spacecraft keeps working."""
    years = float(orbit_of(design)["lifetime"])
    if design["mission"] == "europa" and "shield" not in design["protection"]:
        years /= 2
    return years


def lifetime_factor(design):
    return lifetime_years(design) / orbit_of(design)["lifetime"]


def solar_aging(design):
    """Average solar output over the mission: panels lose 10% a year."""
    p = D.POWER.get(design["power"] or "", None)
    if not p or not p["solar"]:
        return 1.0
    years = lifetime_years(design)
    return (1.0 + 0.9 ** years) / 2


# ---------------------------------------------------------------- meters
def meters(design):
    """The six live meters as (label, value_text, fraction, state).

    state is ok, warn or bad. fraction is 0-1 for the bar.
    """
    m = mission_of(design)
    sandbox = design["difficulty"] == "sandbox"
    out = []

    cost, budget = total_cost(design), m["budget"]
    if sandbox:
        out.append(("Budget", "$%dM spent (no limit)" % cost, 0.0, "ok"))
    else:
        frac = cost / budget
        st = "bad" if frac > 1 else ("warn" if frac > 0.85 else "ok")
        out.append(("Budget", "$%dM / $%dM" % (cost, budget), frac, st))

    mass, cap = total_mass(design), rocket_capacity(design)
    if cap <= 0:
        out.append(("Mass", "%d kg / no rocket" % mass, 1.0, "bad"))
    else:
        frac = mass / cap
        st = "bad" if frac > 1 else ("warn" if frac > 0.9 else "ok")
        out.append(("Mass", "%d / %d kg" % (mass, cap), frac, st))

    made, used = power_made(design), power_used(design)
    frac = used / made if made else 1.0
    st = "bad" if made < used else ("warn" if made < used * 1.1 else "ok")
    out.append(("Power", "%d W made / %d W used" % (made, used), frac, st))

    dm, dl = data_made(design), downlink(design)
    ret = data_returned_frac(design)
    st = "bad" if ret < 0.5 else ("warn" if ret < 0.9 else "ok")
    out.append(("Data", "%.0f Gb/day, %d%% home" % (dm, ret * 100), ret, st))

    reach = D.COMMS[design["comms"]]["reach"][design["mission"]] if design["comms"] else 0
    st = "bad" if reach == 0 else ("warn" if reach < 0.9 else "ok")
    out.append(("Comms", "%d Gb/day link" % dl if design["comms"] else "no antenna",
                reach, st))

    yrs, full = lifetime_years(design), orbit_of(design)["lifetime"]
    st = "ok" if yrs >= full else "warn"
    out.append(("Lifetime", "%.1f / %d years" % (yrs, full), yrs / full, st))
    return out


# ---------------------------------------------------------------- launch check
def launch_check(design):
    """List of {item, ok, why, blocking}. Blocking items lock the Launch button."""
    m, o = mission_of(design), orbit_of(design)
    sandbox = design["difficulty"] == "sandbox"
    items = []

    def add(item, ok, why, blocking=False):
        items.append({"item": item, "ok": ok, "why": why, "blocking": blocking})

    add("Rocket chosen", bool(design["rocket"]),
        "Pick a rocket." if not design["rocket"] else D.ROCKETS[design["rocket"]]["name"],
        blocking=True)
    cap = rocket_capacity(design)
    if design["rocket"] and cap == 0:
        add("Rocket can reach %s" % D.DEST[design["mission"]], False,
            "This rocket can't reach %s at all." % D.DEST[design["mission"]], blocking=True)
    else:
        mass = total_mass(design)
        add("Fits on the rocket", mass <= cap,
            "%d kg on a %d kg rocket" % (mass, cap) if cap else "No rocket yet")
    if not sandbox:
        left = budget_left(design)
        add("Within budget", left >= 0,
            "$%dM left" % left if left >= 0 else "$%dM over budget" % -left, blocking=True)
    add("Power source", bool(design["power"]),
        "Pick a power source." if not design["power"] else D.POWER[design["power"]]["name"],
        blocking=True)
    made, used = power_made(design), power_used(design)
    add("Enough power", made >= used, "%d W made for %d W used" % (made, used))
    add("At least one instrument", len(design["instruments"]) > 0,
        "%d carried" % len(design["instruments"]), blocking=True)
    add("Antenna that reaches Earth", data_returned_frac(design) > 0,
        "Pick an antenna that works at %s." % D.DEST[design["mission"]]
        if data_returned_frac(design) == 0 else "%d%% of data gets home"
        % (data_returned_frac(design) * 100), blocking=True)
    if o["landing"]:
        need = "land_moon" if design["mission"] == "moon" else "land_mars"
        add("Landing system", need in design["protection"],
            "A %s needs a landing system." % o["name"].lower(), blocking=True)
    if "drill" in design["instruments"] and not o["drill_ok"]:
        add("Drill can be used", False, "Orbiters can't drill: it will earn 0 science.")
    return items


def can_launch(design):
    return all(i["ok"] for i in launch_check(design) if i["blocking"])


def launch_succeeds_on_mass(design):
    cap = rocket_capacity(design)
    return cap > 0 and total_mass(design) <= cap


# ---------------------------------------------------------------- science
def instrument_points(design, ids):
    o = orbit_of(design)
    pts = 0
    for i in ids:
        if i == "drill" and not o["drill_ok"]:
            continue
        pts += D.INSTRUMENTS[i]["pts"][design["mission"]]
    return pts


def best_possible_science(mission):
    """Top 4 instruments at the best orbit's science multiplier."""
    best = 0.0
    for oid in D.MISSIONS[mission]["orbits"]:
        o = D.ORBITS[oid]
        pts = sorted((v["pts"][mission] for k, v in D.INSTRUMENTS.items()
                      if k != "drill" or o["drill_ok"]), reverse=True)
        best = max(best, sum(pts[:D.MAX_INSTRUMENTS]) * o["science_x"])
    return best


def top_instrument(mission):
    return max(D.INSTRUMENTS, key=lambda k: D.INSTRUMENTS[k]["pts"][mission])


def science_collected(design, alive=None, solar_x=1.0, science_x=1.0, bonus=0):
    """Science that counts after power, data, lifetime and events."""
    ids = design["instruments"] if alive is None else alive
    raw = instrument_points(design, ids) * orbit_of(design)["science_x"]
    pf = power_ratio(power_made(design, solar_x) * solar_aging(design), power_used(design))
    df = data_returned_frac(design, ids)
    return raw * pf * df * lifetime_factor(design) * science_x + bonus


# ---------------------------------------------------------------- goals
def check_goal(goal_id, design, result, score_pts):
    m = design["mission"]
    if goal_id == "no_damage":
        return result["unprevented"] == 0
    if goal_id == "risky_3star":
        return design["orbit"] == D.RISKY_ORBIT[m] and stars_for(score_pts) >= 3
    if goal_id == "mass_margin":
        cap = rocket_capacity(design)
        return cap > 0 and total_mass(design) <= cap * 0.9
    if goal_id == "power_surplus":
        return power_made(design) >= power_used(design) * 1.1
    if goal_id == "three_instr":
        return len(design["instruments"]) >= 3
    if goal_id == "top_instr":
        return top_instrument(m) in design["instruments"]
    if goal_id == "budget_20":
        return design["difficulty"] == "sandbox" or budget_left(design) >= budget_of(design) * 0.2
    if goal_id == "data_90":
        return data_returned_frac(design) >= 0.9
    return False


# ---------------------------------------------------------------- score
def stars_for(points):
    for cut, s in D.STARS:
        if points >= cut:
            return s
    return 1


def score(design, result, goals=None):
    """Score out of 100.

    result comes from events.run_mission. goals is a list of goal ids
    held by the team (one per role). Returns a dict with total, stars,
    breakdown and goals_met.
    """
    split = D.SCORE_SPLIT
    if result["lost"]:
        return {"total": 0, "stars": 1, "breakdown": {k: 0 for k in split},
                "goals_met": [], "lost": True}

    best = best_possible_science(design["mission"])
    sci = min(split["science"], result["science"] / best * split["science"]) if best else 0

    if design["difficulty"] == "sandbox":
        bud = split["budget"]
    else:
        left_frac = budget_left(design) / budget_of(design)
        bud = max(0.0, min(1.0, left_frac / 0.25)) * split["budget"]

    rel = max(0, split["reliability"] - 5 * result["unprevented"])

    partial = sci + bud + rel
    goals = goals or []
    met = []
    # goals that depend on the final score use the score before goal points
    for g in goals:
        if check_goal(g, design, result, partial + D.GOAL_POINTS * len(goals)):
            met.append(g)
    gp = min(split["goals"], D.GOAL_POINTS * len(met))
    if not goals:
        # solo with no cards: scale the other parts up to 100
        total = partial * 100 / (100 - split["goals"])
    else:
        total = partial + gp
    total = int(round(min(100, total)))
    return {"total": total, "stars": stars_for(total),
            "breakdown": {"science": round(sci), "budget": round(bud),
                          "reliability": rel, "goals": gp},
            "goals_met": met, "lost": False}


def weakest_link(design, result):
    """Key for the single most useful tip."""
    if result["lost"]:
        return "mass" if result.get("lost_reason") == "mass" else "budget"
    made, used = power_made(design), power_used(design)
    if made < used:
        return "power"
    if data_returned_frac(design) < 0.9:
        return "comms"
    for ph in result["phases"]:
        if not ph["prevented"] and ph["effect"] in ("flare", "radiation"):
            return "shield"
        if not ph["prevented"] and ph["effect"] == "dust":
            return "dust"
        if not ph["prevented"] and ph["effect"] == "night":
            return "night"
    return "budget"
