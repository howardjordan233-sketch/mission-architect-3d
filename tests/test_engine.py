from game import data as D
from game import engine as E
from game import events as V


def mars_good():
    d = D.empty_design("mars", "mars_rover")
    d.update(rocket="medium", power="rtg", comms="relay",
             instruments=["spectro", "drill", "radar", "camera"], protection=["land_mars"])
    return d


def moon_good():
    d = D.empty_design("moon", "south_lander")
    d.update(rocket="medium", power="solar_l", battery=True, comms="small_ant",
             instruments=["drill", "spectro", "radar"], protection=["land_moon"])
    return d


def europa_good():
    d = D.empty_design("europa", "europa_flybys")
    d.update(rocket="heavy", power="solar_g", comms="hga",
             instruments=["radar", "magneto", "spectro", "thermal"], protection=["shield"])
    return d


def test_power_ratio_example():
    # Rules: 150 W made for 200 W used means 75% of the science.
    assert E.power_ratio(150, 200) == 0.75
    assert E.power_ratio(300, 200) == 1.0


def test_solar_scales_with_sunlight():
    d = D.empty_design("mars", "mars_rover")
    d["power"] = "solar_l"
    assert E.power_made(d) == 860  # 2000 W x 43%
    d["mission"], d["orbit"] = "europa", "europa_flybys"
    d["power"] = "solar_g"
    assert E.power_made(d) == 700  # 17500 W x 4%, NASA's Clipper figure


def test_cost_and_mass_include_body():
    d = mars_good()
    assert E.total_cost(d) == 200 + 70 + 150 + 8 + 40 + 60 + 50 + 20 + 150
    assert E.total_mass(d) == 800 + 45 + 5 + 25 + 40 + 30 + 15 + 1200


def test_launch_check_blocks_missing_lander():
    d = mars_good()
    d["protection"] = []
    assert not E.can_launch(d)
    d["protection"] = ["land_mars"]
    assert E.can_launch(d)


def test_small_rocket_cannot_reach_mars():
    d = mars_good()
    d["rocket"] = "small"
    assert not E.can_launch(d)


def test_data_limited_design_scores_less():
    good = europa_good()
    weak = europa_good()
    weak["comms"] = "small_ant"
    assert E.data_returned_frac(weak) < 0.3
    rg = V.run_mission(dict(good, difficulty="sandbox"), seed=1)
    rw = V.run_mission(dict(weak, difficulty="sandbox"), seed=1)
    assert rw["science"] < rg["science"] * 0.5


def test_good_designs_score_well():
    for d in (moon_good(), mars_good(), europa_good()):
        d["difficulty"] = "sandbox"
        res = V.run_mission(d, seed=3)
        s = E.score(d, res)
        assert s["stars"] >= 4, (d["mission"], s)


def test_overweight_scores_zero():
    d = mars_good()
    d["power"] = "solar_g"
    d["protection"] = ["land_mars", "shield"]
    d["rocket"] = "medium"
    res = V.run_mission(d, seed=1)
    assert res["lost"] and res["lost_reason"] == "mass"
    assert E.score(d, res)["total"] == 0


def test_europa_without_shield_lasts_half():
    d = europa_good()
    d["protection"] = []
    assert E.lifetime_years(d) == 2


def test_score_is_bounded():
    for seed in range(40):
        for d in (moon_good(), mars_good(), europa_good()):
            res = V.run_mission(d, seed=seed)
            s = E.score(d, res, goals=["no_damage", "mass_margin", "three_instr", "budget_20"])
            assert 0 <= s["total"] <= 100
            assert 1 <= s["stars"] <= 5


def test_meters_has_six():
    assert [m[0] for m in E.meters(mars_good())] == [
        "Budget", "Mass", "Power", "Data", "Comms", "Lifetime"]
