"""Challenge codes like MARS-7Q2K-9PX that store a whole mission.

35 bits written as seven Crockford base-32 characters: 22 for the design,
8 for the seed (0-255), 4 for the secret goal cards and 1 spare. A friend
types the code in and flies the exact same mission, with the same luck and
the same goal cards, so the two scores can be compared fairly.
"""
from game import data as D

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # no I, L, O, U
ROCKET_IDS = [None, "small", "medium", "heavy", "super"]
POWER_IDS = [None, "solar_s", "solar_l", "solar_g", "rtg"]
COMMS_IDS = [None, "small_ant", "hga", "relay"]
INSTR_IDS = ["camera", "spectro", "drill", "radar", "magneto", "thermal"]
PROT_IDS = ["land_moon", "land_mars", "shield", "dust"]
PREFIX = {"moon": "MOON", "mars": "MARS", "europa": "EURO"}
FROM_PREFIX = {v: k for k, v in PREFIX.items()}


CHARS = 7


def cards_to_bits(cards):
    bits = 0
    for i, role in enumerate(D.ROLES):
        ids = [c["id"] for c in D.GOAL_CARDS[role]]
        k = ids.index(cards[role]["id"]) if cards and role in cards else 0
        bits |= (k & 1) << i
    return bits


def bits_to_cards(bits):
    return {role: D.GOAL_CARDS[role][(bits >> i) & 1] for i, role in enumerate(D.ROLES)}


def encode(design, seed, cards=None):
    m = design["mission"]
    bits = 0

    def push(value, width):
        nonlocal bits
        bits = (bits << width) | (value & ((1 << width) - 1))

    push(D.MISSIONS[m]["orbits"].index(design["orbit"]), 1)
    push(D.DIFFICULTY_ORDER.index(design["difficulty"]), 2)
    push(ROCKET_IDS.index(design["rocket"]), 3)
    push(POWER_IDS.index(design["power"]), 3)
    push(1 if design["battery"] else 0, 1)
    push(COMMS_IDS.index(design["comms"]), 2)
    push(sum(1 << i for i, k in enumerate(INSTR_IDS) if k in design["instruments"]), 6)
    push(sum(1 << i for i, k in enumerate(PROT_IDS) if k in design["protection"]), 4)
    push(int(seed) % 256, 8)
    push(cards_to_bits(cards), 4)
    push(0, 1)  # spare
    chars = ""
    for _ in range(CHARS):
        chars = ALPHABET[bits & 31] + chars
        bits >>= 5
    return "%s-%s-%s" % (PREFIX[m], chars[:4], chars[4:])


def decode(code):
    """Returns (design, seed, cards) or raises ValueError for a bad code."""
    text = code.strip().upper().replace(" ", "")
    parts = text.split("-")
    if len(parts) == 2 and len(parts[1]) == CHARS:
        parts = [parts[0], parts[1][:4], parts[1][4:]]
    if len(parts) != 3 or parts[0] not in FROM_PREFIX:
        raise ValueError("Codes look like MARS-7Q2K-9PX")
    # forgive look-alike letters in the body only (MOON keeps its O's)
    body = (parts[1] + parts[2]).replace("O", "0").replace("I", "1").replace("L", "1")
    if len(body) != CHARS or any(c not in ALPHABET for c in body):
        raise ValueError("Codes look like MARS-7Q2K-9PX")
    bits = 0
    for c in body:
        bits = (bits << 5) | ALPHABET.index(c)

    fields = []
    for width in (1, 4, 8, 4, 6, 2, 1, 3, 3, 2, 1):  # reverse order of encode
        fields.append(bits & ((1 << width) - 1))
        bits >>= width
    _spare, card_bits, seed, prot, instr, comms, batt, power, rocket, diff, orbit = fields
    m = FROM_PREFIX[parts[0]]
    if rocket >= len(ROCKET_IDS) or power >= len(POWER_IDS) or diff >= 3:
        raise ValueError("That code doesn't match a real design")
    d = D.empty_design(m, D.MISSIONS[m]["orbits"][orbit], D.DIFFICULTY_ORDER[diff])
    d["rocket"] = ROCKET_IDS[rocket]
    d["power"] = POWER_IDS[power]
    d["battery"] = bool(batt)
    d["comms"] = COMMS_IDS[comms]
    d["instruments"] = [k for i, k in enumerate(INSTR_IDS) if instr & (1 << i)]
    d["protection"] = [k for i, k in enumerate(PROT_IDS) if prot & (1 << i)]
    return d, seed, bits_to_cards(card_bits)
