"""Team mode: roles, secret goal cards and the Go/No-Go vote."""
import random

from game import data as D

# Who holds which roles for each team size.
SPLITS = {
    1: [["director", "engineer", "science", "comms"]],
    2: [["director", "science"], ["engineer", "comms"]],
    3: [["director", "comms"], ["engineer"], ["science"]],
    4: [["director"], ["engineer"], ["science"], ["comms"]],
}


def deal_roles(player_count, names=None):
    """Returns a list of players: {name, roles}."""
    n = max(1, min(4, int(player_count)))
    names = list(names or [])
    players = []
    for i, roles in enumerate(SPLITS[n]):
        name = names[i] if i < len(names) and names[i] else "Player %d" % (i + 1)
        players.append({"name": name, "roles": list(roles)})
    return players


def deal_goal_cards(seed=None):
    """One secret goal card per role: {role: {id, text}}."""
    rng = random.Random(seed)
    return {role: rng.choice(D.GOAL_CARDS[role]) for role in D.ROLES}


def controls(player):
    """Categories a player may change (plus 'orbit')."""
    out = []
    for r in player["roles"]:
        out.extend(D.ROLE_INFO[r]["controls"])
    return out


def owner_of(category, players):
    """Index of the player who controls a category."""
    for i, p in enumerate(players):
        if category in controls(p):
            return i
    return 0


def check_goals(cards, design, result, score_result):
    """Which roles met their card. Uses score_result['goals_met']."""
    met = set(score_result.get("goals_met", []))
    return {role: card["id"] in met for role, card in cards.items()}


def go_no_go(votes):
    """votes: {role: (go_bool, reason)}. Passes only if every role says Go.

    Returns (passed, [reasons from No-Go voters]).
    """
    reasons = []
    for role in D.ROLES:
        if role not in votes:
            reasons.append("%s has not voted" % D.ROLE_INFO[role]["name"])
            continue
        go, why = votes[role]
        if not go:
            reasons.append("%s: %s" % (D.ROLE_INFO[role]["name"], why or "No reason given"))
    return (len(reasons) == 0, reasons)


NO_GO_REASONS = [
    "Over budget or too close to it",
    "Too heavy for the rocket",
    "Not enough power",
    "Too little data gets home",
    "Missing protection",
    "My goal card isn't met",
]
