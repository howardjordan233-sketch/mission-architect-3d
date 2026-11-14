"""The post-mission report: what you chose, what happened and why."""
from game import data as D
from game import engine as E


def reasons(design, result, score_result):
    """Three plain-English reasons the mission went the way it did."""
    out = []
    m = design["mission"]
    if result["lost"]:
        if result.get("lost_reason") == "mass":
            out.append("The spacecraft weighed %d kg but the rocket could only lift %d kg to %s."
                       % (E.total_mass(design), E.rocket_capacity(design), D.DEST[m]))
            out.append("Heavier parts (landing systems, big solar arrays, shielding) need a "
                       "bigger rocket, which costs more.")
        else:
            out.append("The rocket failed at launch. Even reliable rockets fail sometimes.")
            out.append("A more reliable rocket lowers the odds, but never to zero.")
        out.append("Every mission starts with getting off the ground safely.")
        return out

    made, used = E.power_made(design), E.power_used(design)
    if made < used:
        out.append("Power was short: %d W made for %d W used, so instruments ran only %d%% "
                   "of the time." % (made, used, E.power_ratio(made, used) * 100))
    else:
        out.append("Power was healthy: %d W made for %d W used." % (made, used))

    ret = E.data_returned_frac(design, result["alive"])
    if ret < 0.9:
        out.append("Only %d%% of the data reached Earth. A stronger antenna would have "
                   "brought more science home." % (ret * 100))
    else:
        out.append("%d%% of the data reached Earth." % (ret * 100))

    bad = [p for p in result["phases"] if p["bad"] and not p["prevented"]]
    saved = [p for p in result["phases"] if p["bad"] and p["prevented"]]
    if bad:
        out.append("%s hurt the mission: %s" % (bad[0]["event"], bad[0]["message"]))
    elif saved:
        out.append("Good planning paid off: %s" % saved[0]["message"])
    else:
        out.append("The mission had calm luck. Next time, check whether you over-protected "
                   "or could afford another instrument.")
    return out[:3]


def make_report(design, result, score_result, cards=None, players=None, code=""):
    """Returns the report as plain text. Never writes a file."""
    m = D.MISSIONS[design["mission"]]
    o = D.ORBITS[design["orbit"]]
    lines = []
    lines.append("MISSION REPORT  %s" % code)
    lines.append("=" * 44)
    lines.append("Objective: %s (%s)" % (m["goal"], m["name"]))
    lines.append("Orbit: %s   Difficulty: %s" % (o["name"],
                                                D.DIFFICULTIES[design["difficulty"]]["name"]))
    if players:
        lines.append("Team: " + ", ".join(p["name"] for p in players))
    lines.append("")
    lines.append("CHOICES")
    if design["rocket"]:
        lines.append("  Rocket: " + D.ROCKETS[design["rocket"]]["name"])
    if design["power"]:
        lines.append("  Power: " + D.POWER[design["power"]]["name"]
                     + (" + battery" if design["battery"] else ""))
    lines.append("  Instruments: " + (", ".join(D.INSTRUMENTS[i]["name"]
                                                for i in design["instruments"]) or "none"))
    if design["comms"]:
        lines.append("  Comms: " + D.COMMS[design["comms"]]["name"])
    lines.append("  Protection: " + (", ".join(D.PROTECTION[p]["name"]
                                               for p in design["protection"]) or "none"))
    lines.append("  Cost $%dM of $%dM, mass %d kg" % (E.total_cost(design), m["budget"],
                                                       E.total_mass(design)))
    lines.append("")
    lines.append("WHAT HAPPENED")
    for p in result["phases"]:
        mark = "OK " if p["prevented"] or not p["bad"] else "HIT"
        lines.append("  [%s] %s: %s" % (mark, p["phase"], p["message"]))
    lines.append("")
    b = score_result["breakdown"]
    lines.append("SCORE %d/100  %s" % (score_result["total"], "*" * score_result["stars"]))
    lines.append("  Science %d  Budget %d  Reliability %d  Role goals %d"
                 % (b["science"], b["budget"], b["reliability"], b["goals"]))
    if cards:
        met = set(score_result.get("goals_met", []))
        for role, card in cards.items():
            lines.append("  %s %s: %s" % ("[x]" if card["id"] in met else "[ ]",
                                          D.ROLE_INFO[role]["name"], card["text"]))
    lines.append("")
    lines.append("WHY IT WENT THIS WAY")
    for i, r in enumerate(reasons(design, result, score_result), 1):
        lines.append("  %d. %s" % (i, r))
    nasa = D.NASA[design["mission"]]
    lines.append("")
    lines.append("YOU VS. NASA: %s (%s)" % (nasa["mission"], nasa["when"]))
    lines.append("  Power: %s   Rocket: %s" % (nasa["power"], nasa["rocket"]))
    lines.append("  Lesson: " + nasa["lesson"])
    return "\n".join(lines)
