import os

os.environ["MA3D_NO_FILE"] = "1"

import pytest  # noqa: E402

from game import codes, data as D, engine as E, events as V  # noqa: E402
from game import leaderboard, patch, report, storage, team  # noqa: E402
from tests.test_engine import mars_good, moon_good, europa_good  # noqa: E402


def test_codes_round_trip():
    for d in (mars_good(), moon_good(), europa_good()):
        for seed in (0, 1, 77, 255):
            cards = team.deal_goal_cards(seed)
            code = codes.encode(d, seed, cards)
            assert len(code) == len("MARS-7Q2K-9PX")
            back, s, back_cards = codes.decode(code)
            assert back_cards == cards
            assert s == seed
            for k in ("mission", "orbit", "difficulty", "rocket", "power", "battery", "comms"):
                assert back[k] == d[k]
            assert sorted(back["instruments"]) == sorted(d["instruments"])
            assert sorted(back["protection"]) == sorted(d["protection"])


def test_code_forgives_case_and_lookalikes():
    code = codes.encode(moon_good(), 12)
    assert codes.decode(code.lower())[1] == 12
    assert codes.decode(code.replace("-", " - ", 1))[1] == 12
    assert codes.decode(code[:5] + code[5:].replace("0", "O"))[1] == 12


def test_bad_code_raises():
    for bad in ("", "HELLO", "MARS-12", "PLUTO-AAAA-AAA", "MARS-UUUU-UUU", "MARS-AAAA-AA"):
        with pytest.raises(ValueError):
            codes.decode(bad)


def test_same_code_same_outcome():
    d = mars_good()
    code = codes.encode(d, 42)
    d2, seed, _ = codes.decode(code)
    a = V.run_mission(d, seed=42)
    b = V.run_mission(d2, seed=seed)
    assert a["science"] == b["science"]


def test_roles_cover_everything():
    for n in range(1, 5):
        players = team.deal_roles(n, ["A", "B"])
        roles = [r for p in players for r in p["roles"]]
        assert sorted(roles) == sorted(D.ROLES)
        assert len(players) == n
        for cat in D.CATEGORIES + ["orbit"]:
            assert 0 <= team.owner_of(cat, players) < n
    assert team.deal_roles(2, ["Ana"])[1]["name"] == "Player 2"


def test_goal_cards_one_per_role_and_seeded():
    a = team.deal_goal_cards(5)
    assert set(a) == set(D.ROLES)
    assert a == team.deal_goal_cards(5)


def test_go_no_go():
    all_go = {r: (True, "") for r in D.ROLES}
    assert team.go_no_go(all_go) == (True, [])
    votes = dict(all_go, engineer=(False, "Too heavy for the rocket"))
    ok, why = team.go_no_go(votes)
    assert not ok and "Too heavy" in why[0]
    ok, why = team.go_no_go({"director": (True, "")})
    assert not ok and len(why) == 3


def test_goals_add_points():
    d = mars_good()
    r = V.run_mission(dict(d, difficulty="sandbox"), seed=1)
    plain = E.score(d, r, goals=["three_instr", "top_instr"])
    assert set(plain["goals_met"]) == {"three_instr", "top_instr"}
    assert plain["breakdown"]["goals"] == 10


def test_report_has_three_reasons_and_no_file():
    for d in (mars_good(), moon_good(), europa_good()):
        r = V.run_mission(d, seed=9)
        s = E.score(d, r)
        assert len(report.reasons(d, r, s)) == 3
        text = report.make_report(d, r, s, cards=team.deal_goal_cards(1), code="X")
        assert "WHY IT WENT THIS WAY" in text and "YOU VS. NASA" in text


def test_report_explains_overweight():
    d = mars_good()
    d["protection"] = ["land_mars", "shield"]
    d["power"] = "solar_g"
    r = V.run_mission(d, seed=1)
    assert "rocket could only lift" in report.reasons(d, r, E.score(d, r))[0]


def test_leaderboard_top_ten():
    storage.clear()
    for i in range(14):
        leaderboard.add("mars", "P%d" % i, i * 5, 3)
    board = leaderboard.get("mars")
    assert len(board) == 10 and board[0]["score"] == 65
    assert leaderboard.add("mars", "Best", 99, 5) == 1
    assert leaderboard.add("mars", "Worst", 0, 1) is None
    assert leaderboard.get("moon") == []


def test_patch_design_is_data():
    d = europa_good()
    p = patch.patch_design(d, {"stars": 4, "total": 81})
    assert p["stars"] == 4 and p["icons"][0] == "panel" and len(p["icons"]) == 5
    assert "EUROPA" in p["bottom_text"]
