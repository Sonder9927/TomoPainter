from pathlib import Path

from icecream import ic
import pandas as pd

from .area import AreaPainter
from .dispersion import gmt_plot_dispersion_curves as plot_dc
from tomopainter.rose import area_hull_files, calc_lab
from .phase import PhasePainter
from .s_wave import VsPainter


class TomoPainter:
    def __init__(self) -> None:
        self.images = Path("images")
        self.region = [115, 122.5, 27.9, 34.3]
        dp = Path("data")
        self.txt = dp / "txt"
        self.vs = pd.read_csv(dp / "vs.csv")
        mm = pd.read_csv(dp / "misfit_moho.csv")
        self.misfit = mm[["x", "y", "misfit"]]
        mm["moho"] = -abs(mm["moho"])
        self.moho = mm[["x", "y", "moho"]]
        self.mlf = self.txt / "moho_lab.csv"
        self._init_funcs()
        self.eles = {"tect": 0, "clip": True, "sta": None}

    def plot(self, idt, *args, **kwargs):
        custom, elements = self._sep_args(kwargs)
        self.paint_funcs[idt](*args, **custom, eles=elements)

    def map(self, idt):
        self.paint_funcs[idt]()

    def _sep_args(self, params: dict):
        eles = {
            key: self.eles[key] if params.get(key) is None else params.pop(key)
            for key in self.eles.keys()
        }
        if eles["sta"]:  # pyright:ignore
            eles["sta"] = pd.read_csv(  # pyright:ignore
                "data/station.lst",
                usecols=[1, 2],
                names=["x", "y"],
                header=None,
                delim_whitespace=True,
            )
        return params, eles

    # TODO
    def _init_funcs(self):
        """set functions to match idt, not a good way, uncomplete"""
        # plot area figs
        ap = AreaPainter(self.region, "data/per_evt_sta.csv")
        ap_funcs = {
            "area": ap.area_map,
            "model": ap.model,
            "pe": ap.per_evt,
            "period event": ap.per_evt,
            "sites": ap.sites,
            "rays": ap.rays,
        }

        # plot phase figs
        cptcf = {"cmap": "jet", "reverse": True}
        # cptcf = {"cpt": "Vc_1.8s.cpt"}
        ps_file = self.txt / "periods_series_jet.json"
        php = PhasePainter(self.region, ps_file, cptcf)
        php_funcs = {
            "vel": php.vel,
            "as": php.std,
            "std": php.std,
            "diff": php.diff,
            "cb": php.checkboard,
        }

        # plot dispersion curves figs
        dc_funcs = {"dc": plot_dc, "dispersion curves": plot_dc}

        # plot mcmc figs
        self.vsp = VsPainter(self.region, self.vs, self.mlf)
        vsp_funcs = {
            "depths": self._vs_depths,
            "profiles": self.vsp.profiles,
            "misfit": self._misfit,
        }

        self.paint_funcs = {
            key: value
            for dt in [ap_funcs, php_funcs, vsp_funcs, dc_funcs]
            for key, value in dt.items()
        }

    def _misfit(self, *, eles):
        self.vsp.misfit(self.misfit, eles=eles)

    def _vs_depths(self, *, eles, **params):
        depths = params.get("depths")
        dep_filter = params.get("dep_filter")
        if any([depths, dep_filter is not None]):
            ave = params.get("ave") is not None
            self.vsp.depths(
                ave, depths=depths, dep_filter=dep_filter, eles=eles
            )

    def profiles(self, dep=-200):
        self.vsp.profiles(dep)

    # def area(self, *args):
    #     self._mkdir("area_figs")
    #     for tt in args:
    #         if tt == "area":
    #             self.ap.area_map()
    #         elif tt == "per_evt":
    #             self.ap.per_evt()
    #         elif tt == "sites":
    #             self.ap.sites()
    #         elif tt == "rays":
    #             self.ap.rays()
    #         else:
    #             raise NotImplementedError

    # def phase(self, idt="vel", method="tpwt", *, periods=None, dcheck=2.0):
    #     self._mkdir("ant_figs", "tpwt_figs")
    #     if idt == "vel":
    #         self.php.vel(method, idt, periods=periods)
    #     elif idt == "cb":
    #         self.php.vel(method, idt, periods=periods, dcheck=dcheck)
    #     elif idt == "std":
    #         self.php.std(periods)
    #     elif idt == "diff":
    #         self.php.diff(periods)
    #     else:
    #         raise NotImplementedError(f"Cannot identify {idt}")

    # def dispersion(self):
    #     self._mkdir("dispersion_curves")
    #     gmt_plot_dispersion_curves(self.misfit)

    # def mcmc(self, idt, **kwargs):
    #     self._mkdir("mc_figs/depth", "mc_figs/profile")
    #     if idt == "misfit":
    #         self.vsp.misfit(self.misfit)
    #     elif idt == "profile":
    #         dep = kwargs.get("dep") or -200
    #         self.vsp.profiles(dep)
    #     elif idt == "depth":
    #         depths = kwargs.get("depths")
    #         dep_filter = kwargs.get("dep_filter")
    #         if any([depths, dep_filter is not None]):
    #             ave = kwargs.get("ave")
    #             self.vsp.depths(ave, depths=depths, dep_filter=dep_filter)
    #         else:
    #             raise ValueError("No valid `depths` for hpanel of Vs")
    #     else:
    #         raise NotImplementedError(f"Cannot identify {idt}")

    def initialize(self, *, lab_range=None):
        moho_range = [self.moho["moho"].min(), self.moho["moho"].max()]
        lab_range = lab_range or [-moho_range[1] - 10, -200]
        calc_lab(self.vs, self.moho, self.mlf, lab_range)
        # make hull of stas in the area
        area_hull_files(self.region, outdir=self.txt)

    def print_info(self, *, misfit_limit=0.5, span=None):
        # filter grid where misfit > limit
        misfit_limit = self.misfit[self.misfit["misfit"] > misfit_limit]
        ic(misfit_limit)
        moho_range = [self.moho["moho"].min(), self.moho["moho"].max()]
        ic(moho_range)
        vs_crust = self.vs[self.vs["z"] > moho_range[1]]
        ic(vs_crust["v"].mean())
        if span is not None:
            vs_mantle = self.vs[self.vs["z"] < moho_range[0]]
            for z in span:
                pace = [moho_range[0], -abs(z)]
                vs_range = vs_mantle[vs_mantle["z"] > pace[1]]
                vs_ave = vs_range["v"].mean()
                ic(pace, vs_ave)

    # def _mkdir(self, *args):
    #     for target in args:
    #         if not (tt := self.images / target).exists():
    #             tt.mkdir(parents=True)
