from pathlib import Path
from tomopainter.rose import path

import matplotlib.pyplot as plt
import pandas as pd
from tomopainter.rose.query import DataQueryer

from .gmt import (
    plot_area_map,
    plot_evt_sites,
    plot_rays,
    plot_model,
)


class AreaPainter:
    def __init__(self, queryer: DataQueryer, region) -> None:
        self.queryer = queryer
        self.region = region
        self.afigs = path.mkdir("images/area_figs")
        self.mfigs = path.mkdir("images/model_figs")
        self.idts = {
            "area": self._area,
            "model": self._model,
            "sites": self._sites,
            "rays": self._rays,
            "per_evt": self._per_evt,
        }

    def _area(self, vici_region=None):
        vici_region = vici_region or [110, 125, 25, 40]
        regions = [vici_region, self.region]
        plot_area_map(regions, self.afigs / "area.png")

    def _per_evt(self):
        return
        data = self.pes.groupby("per").size().to_dict()
        _plot_per_evt(data, self.afigs / "perNum_vel.png")

    def _sites(self):
        return
        sites = self.pes[["evt"]].drop_duplicates()
        plot_evt_sites(sites, self.region, self._fig("evt_sites.png"))

    def _rays(self):
        return
        rays = self.pes[["evt", "sta"]].drop_duplicates()
        plot_rays(self.regions, rays, self._fig("rays_cover.png"))

    def paint(self, idt, pars=None):
        self.idts[idt](pars)

    def _model(self, pars):
        seriesby = {
            "sedthk": [0, 2, 0.1],
            "rf_moho": [27, 38, 0.1],
            "poisson": [1.65, 1.85, 0.01],
            "mc_moho": [27, 38, 0.1],
            "mc_misfit": [0, 1, 0.01],
        }
        idts = pars.get("idts") or seriesby.keys()
        table = "model"
        for idt in idts:
            cpt = {
                "series": seriesby[idt],
                "cmap": "hot" if "misfit" in idt else "jet",
            }
            df = self.queryer.query(table, usecols=[idt])
            plot_model(df, self.region, cpt, self.mfigs / f"{idt}.png")


# class AreaPainter:
#     def __init__(self, region, pesf) -> None:
#         self.regions = [[110, 125, 25, 40], region]
#         self.figs = Path("images/area_figs")
#         self.pes = pd.read_csv(pesf)

#     def area_map(self):
#         plot_area_map(self.regions, self._fig("area.png"))

#     def model(self):
#         plot_model(self.regions[1], self._fig("model.png"))

#     def per_evt(self):
#         data = self.pes.groupby("per").size().to_dict()
#         _plot_per_evt(data, self._fig("perNum_vel.png"))

#     def sites(self):
#         sites = self.pes[["evt"]].drop_duplicates()
#         plot_evt_sites(sites, self.regions[1], self._fig("evt_sites.png"))

#     def rays(self):
#         rays = self.pes[["evt", "sta"]].drop_duplicates()
#         plot_rays(self.regions, rays, self._fig("rays_cover.png"))

#     def _fig(self, fn) -> str:
#         if not self.figs.exists():
#             self.figs.mkdir(parents=True)
#         return str(self.figs / fn)


def gmt_plot_area(region, pesf, onlymap=True):
    vicinity = [110, 125, 25, 40]
    ip = Path("images/area_figs")

    # plot area map with topo
    plot_area_map([vicinity, region], str(ip / "area.png"))
    if onlymap:
        return
    pes = pd.read_csv(pesf)
    _plot_per_evt(pes.groupby("per").size().to_dict(), ip / "perNum_vel.png")
    rays = pes[["evt", "sta"]].drop_duplicates()
    sites = rays[["evt"]].drop_duplicates()
    plot_evt_sites(sites, region, str(ip / "evt_sites.png"))
    plot_rays([vicinity, region], rays, str(ip / "rays_cover.png"))


def _plot_per_evt(data: dict, fn):
    pers = [25, 30] + [35, 40, 45, 50, 60, 70, 80, 90, 100, 111, 125, 143]
    pns = []
    vels_res = []
    for per in pers:
        pns.append(data[per])
        vel = pd.read_csv(
            f"grids/tpwt_grids/tpwt_vel_{per}.grid",
            header=None,
            delim_whitespace=True,
            usecols=[2],
            names=["vel"],
        )
        vels_res.append(vel["vel"].mean())

    vels_init = (
        [3.365, 3.43]
        + [3.51, 3.55, 3.57, 3.59]
        + [3.63, 3.67, 3.71, 3.75, 3.79, 3.82, 3.85, 3.92]
    )

    fig = plt.figure(figsize=(10, 6))
    ax1 = fig.add_subplot(111)
    ax1.bar(pers, pns, width=4)
    ax1.set_ylabel("Number of Ray")
    ax2 = ax1.twinx()
    # ax2.plot(pers, vels_init, "b", label="Vel Init")
    ax2.plot(pers, vels_res, "r", label="Average Phv")
    ax2.set_ylabel("Velocity")
    ax2.legend(loc="upper right")
    fig.savefig(fn)
