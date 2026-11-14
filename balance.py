"""Prints average score for smart, cheap and careless designs per mission.

Run: python balance.py
"""
from game import data as D
from game import engine as E
from game import events as V

DESIGNS = {
    "moon": {
        "smart": dict(orbit="south_lander", rocket="medium", power="solar_l", battery=True,
                      comms="small_ant", instruments=["drill", "spectro", "camera"],
                      protection=["land_moon"]),
        "lander 4": dict(orbit="south_lander", rocket="medium", power="solar_l", battery=True,
                         comms="small_ant", instruments=["drill", "spectro", "radar", "camera"],
                         protection=["land_moon"]),
        "orbiter": dict(orbit="polar_orbiter", rocket="medium", power="solar_l",
                        comms="small_ant", instruments=["spectro", "radar", "camera", "thermal"],
                        protection=[]),
        "careless": dict(orbit="south_lander", rocket="heavy", power="solar_s",
                         comms="small_ant", instruments=["camera"], protection=["land_moon"]),
    },
    "mars": {
        "smart": dict(orbit="mars_rover", rocket="medium", power="rtg", comms="relay",
                      instruments=["spectro", "drill", "radar", "camera"],
                      protection=["land_mars"]),
        "solar rover": dict(orbit="mars_rover", rocket="medium", power="solar_l",
                            comms="relay", instruments=["spectro", "drill", "radar", "camera"],
                            protection=["land_mars"]),
        "orbiter": dict(orbit="mars_orbiter", rocket="medium", power="solar_l", comms="hga",
                        instruments=["spectro", "radar", "camera", "thermal"], protection=[]),
        "careless": dict(orbit="mars_rover", rocket="heavy", power="solar_s",
                         comms="small_ant", instruments=["camera", "magneto"],
                         protection=["land_mars"]),
    },
    "europa": {
        "smart": dict(orbit="europa_flybys", rocket="heavy", power="solar_g", comms="hga",
                      instruments=["radar", "magneto", "spectro", "thermal"],
                      protection=["shield"]),
        "low orbit": dict(orbit="europa_low", rocket="heavy", power="solar_g", comms="hga",
                          instruments=["radar", "magneto", "spectro", "thermal"],
                          protection=["shield"]),
        "no shield": dict(orbit="europa_flybys", rocket="heavy", power="solar_g", comms="hga",
                          instruments=["radar", "magneto", "spectro", "thermal"],
                          protection=[]),
        "careless": dict(orbit="europa_low", rocket="heavy", power="solar_l",
                         comms="small_ant", instruments=["camera", "drill"], protection=[]),
    },
}


def main(runs=200):
    for mission, designs in DESIGNS.items():
        print("== %s (budget $%dM)" % (mission.upper(), D.MISSIONS[mission]["budget"]))
        for label, picks in designs.items():
            d = D.empty_design(mission, picks["orbit"])
            d.update({k: v for k, v in picks.items() if k != "orbit"})
            ok = E.can_launch(d)
            totals = []
            for seed in range(runs):
                r = V.run_mission(d, seed=seed)
                totals.append(E.score(d, r)["total"])
            avg = sum(totals) / len(totals)
            print("  %-12s launch=%-5s cost=$%4dM mass=%5d/%5d  avg=%5.1f  stars=%d"
                  % (label, ok, E.total_cost(d), E.total_mass(d), E.rocket_capacity(d),
                     avg, E.stars_for(avg)))


if __name__ == "__main__":
    main()
