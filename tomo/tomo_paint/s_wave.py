from tqdm import tqdm

from .gmt import plot_vs_hpanel, plot_vs_vpanel


def gmt_plot_vs(gv, targets: dict):
    dps = targets.get("depths")
    dft = targets.get("dep_filter")
    if any([dps, dft is not None]):
        _vs_hpanel(gv, {"depths": dps, "dep_filter": dft})
    if targets.get("profile"):
        _vs_vpanel(gv)


def _vs_hpanel(gv, dep):
    for ave in [False, True]:
        for _, grid, fn in tqdm(gv.depths_data("tomo", ave, **dep)):
            plot_vs_hpanel(grid, gv.hregion, fn, ave=ave)


def _vs_vpanel(gv):
    import json

    ave = True
    params = {"hregion": gv.hregion}
    with gv.profile.open() as f:
        profiles = json.load(f)
    for idt, lls in profiles.items():
        for ll in lls:
            path, fn = gv.init_path(ll, idt)
            params |= zip(
                ["idt", "line", "path", "fname"], [idt, ll, path, fn]
            )
            params |= {"moho": gv.track_border("moho", path)}
            params |= {"lab": gv.track_border("lab", path)}
            plot_vs_vpanel(gv.track_vs(path), **params)
            plot_vs_vpanel(gv.track_vs(path, ave), **params, ave=ave)
