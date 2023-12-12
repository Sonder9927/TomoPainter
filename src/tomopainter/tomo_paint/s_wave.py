from tomopainter.rose import GridVs, DataQueryer, path
from tqdm import tqdm
from pathlib import Path

from .gmt import plot_vs_hpanel, plot_vs_vpanel


class SwavePainter:
    def __init__(self, queryer: DataQueryer, hregion) -> None:
        self.queryer = queryer
        self.hregion = hregion
        self.idts = {
            "depths": self.paint_depths,
            "profiles": self.paint_profiles,
        }
        self.fig_dir = Path("images/swave_figs")

    def paint(self, idt, prs: dict):
        method = prs["method"]
        vs_df = self.queryer.query("swave", usecols=["depth", f"{method}_vs"])
        mohoby = {"rj": "rf_moho", "mc": "mc_moho"}
        ml_df = self.queryer.query("model", usecols=[mohoby[method], "lab"])
        gv = GridVs(method, self.hregion, vs_df, ml_df)
        self.idts[idt](gv, prs.get("depths"), prs.get("ave"))

    def paint_depths(self, gv: GridVs, depths, ave):
        path.mkdir(self.fig_dir / f"{gv.method}" / "depths")
        for _, grid, fn in tqdm(gv.depths_data("tomo", depths, ave)):
            plot_vs_hpanel(grid, gv.hregion, fn, ave)

    def paint_profiles(self, gv: GridVs, depth, ave=False):
        from tomopainter.rose import idt_profiles

        dep = depth or 60
        dep = -abs(dep)
        params = {"hregion": self.hregion, "dep": dep, "ave": ave}
        for idt, lls in idt_profiles(gv.profile, idt=True):
            for ll in lls:
                path, fn = gv.init_path(ll, idt)
                params |= zip(
                    ["idt", "line", "path", "fname"], [idt, ll, path, fn]
                )
                params |= {"moho": gv.track_border("moho", path)}
                params |= {"lab": gv.track_border("lab", path)}
                plot_vs_vpanel(gv.track_vs(path, ave=ave), **params)


class VsPainter:
    def __init__(self, region, vs, mlf) -> None:
        self.gv = GridVs(region, vs, mlf)

    def misfit(self, grid, eles):
        plot_misfit(grid, self.gv.hregion, "images/mc_figs/misfit.png", eles)

    def depths(self, ave, eles, **dps):
        for _, grid, fn in tqdm(self.gv.depths_data("tomo", ave, **dps)):
            plot_vs_hpanel(grid, self.gv.hregion, fn, ave=ave, eles=eles)

    def profiles(self, dep=-200, eles=None):
        from tomopainter.rose import idt_profiles

        # ave = True
        params = {"hregion": self.gv.hregion, "dep": dep}
        for idt, lls in idt_profiles(self.gv.profile, idt=True):
            for ll in lls:
                path, fn = self.gv.init_path(ll, idt)
                params |= zip(
                    ["idt", "line", "path", "fname"], [idt, ll, path, fn]
                )
                params |= {"moho": self.gv.track_border("moho", path)}
                params |= {"lab": self.gv.track_border("lab", path)}
                plot_vs_vpanel(self.gv.track_vs(path), **params)
                # plot_vs_vpanel(self.gv.track_vs(path, ave), **params, ave=ave)


# def gmt_plot_vs(gv, targets: dict):
#     dps = targets.get("depths")
#     dft = targets.get("dep_filter")
#     if any([dps, dft is not None]):
#         _vs_hpanel(gv, {"depths": dps, "dep_filter": dft})
#     if targets.get("profile"):
#         _vs_vpanel(gv)


# def _vs_hpanel(gv, dep):
#     for ave in [False, True]:
#         for _, grid, fn in tqdm(gv.depths_data("tomo", ave, **dep)):
#             plot_vs_hpanel(grid, gv.hregion, fn, ave=ave)


# def _vs_vpanel(gv):
#     import json

#     ave = True
#     params = {"hregion": gv.hregion}
#     with gv.profile.open() as f:
#         profiles = json.load(f)
#     for idt, lls in profiles.items():
#         for ll in lls:
#             path, fn = gv.init_path(ll, idt)
#             params |= zip(
#                 ["idt", "line", "path", "fname"], [idt, ll, path, fn]
#             )
#             params |= {"moho": gv.track_border("moho", path)}
#             params |= {"lab": gv.track_border("lab", path)}
#             plot_vs_vpanel(gv.track_vs(path), **params)
#             plot_vs_vpanel(gv.track_vs(path, ave), **params, ave=ave)
