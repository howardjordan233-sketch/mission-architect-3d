from game import data as D
from game import events as V
from tests.test_engine import mars_good, moon_good, europa_good


def test_same_seed_same_story():
    a = V.run_mission(mars_good(), seed=7)
    b = V.run_mission(mars_good(), seed=7)
    assert [p["message"] for p in a["phases"]] == [p["message"] for p in b["phases"]]


def test_rtg_survives_dust_storm():
    d = mars_good()
    for seed in range(60):
        r = V.run_mission(d, seed=seed)
        for p in r["phases"]:
            if p["effect"] == "dust":
                assert p["prevented"]


def test_solar_rover_hurt_by_dust():
    d = mars_good()
    d["power"] = "solar_l"
    hit = 0
    for seed in range(60):
        r = V.run_mission(d, seed=seed)
        if any(p["effect"] == "dust" and not p["prevented"] for p in r["phases"]):
            hit += 1
            assert "Nuclear" in [p for p in r["phases"] if p["effect"] == "dust"][0]["message"]
    assert hit > 5


def test_unshielded_europa_loses_instruments():
    d = europa_good()
    d["protection"] = []
    r = V.run_mission(d, seed=2)
    assert len(r["alive"]) < len(d["instruments"])
    assert any(p["effect"] == "radiation" and not p["prevented"] for p in r["phases"])


def test_lunar_night_battery():
    r = V.run_mission(moon_good(), seed=4)
    night = [p for p in r["phases"] if p["effect"] == "night"]
    assert night and night[0]["prevented"]


def test_sandbox_has_no_bad_events():
    for d in (mars_good(), moon_good(), europa_good()):
        d["difficulty"] = "sandbox"
        r = V.run_mission(d, seed=1)
        assert r["unprevented"] == 0


def test_every_message_is_text():
    for seed in range(20):
        for d in (mars_good(), moon_good(), europa_good()):
            for p in V.run_mission(d, seed=seed)["phases"]:
                assert p["phase"] in V.PHASES and len(p["message"]) > 10
                assert p["effect"] in ("failure", "flare", "radiation", "rough_landing",
                                       "dust", "night", "discovery", "none")
