import json

from tqdm import tqdm

from .gmt import plot_as, plot_diff, plot_vel


class PhasePainter:
    def __init__(self, queryer, region) -> None:
        from tomopainter.rose import GridPhv

        cptcf = {"cmap": "jet", "reverse": True}
        # cptcf = {"cpt": "Vc_1.8s.cpt"}
        ps_file = "data/txt/periods_series_jet.json"
        self.region = region
        with open(ps_file) as f:
            per_se_pairs = json.load(f)
        self.periods = [int(i) for i in per_se_pairs.keys()]
        self.gps: list[GridPhv] = [
            GridPhv(p, s) for p, s in per_se_pairs.items()
        ]
        self.cptcf = cptcf
        self.idts = ["vel", "std", "cb", "diff"]


class OldPhasePainter:
    def __init__(self, queryer, region) -> None:
        from tomopainter.rose import GridPhv

        cptcf = {"cmap": "jet", "reverse": True}
        # cptcf = {"cpt": "Vc_1.8s.cpt"}
        ps_file = "data/txt/periods_series_jet.json"
        self.region = region
        with open(ps_file) as f:
            per_se_pairs = json.load(f)
        self.periods = [int(i) for i in per_se_pairs.keys()]
        self.gps: list[GridPhv] = [
            GridPhv(p, s) for p, s in per_se_pairs.items()
        ]
        self.cptcf = cptcf

    def vel(self, method, *, periods=None, eles):
        for gp in self._gps(periods):
            vel = gp.grid_file(method, "vel")
            if vel.exists():
                cptcf = {"series": gp.series}
                cptcf |= self.cptcf
                fn = gp.fig_name(method, "vel")
                plot_vel(vel, self.region, fn, eles, cptcf)

    def checkboard(self, method="tpwt", *, periods=None, dcheck=2.0, eles):
        for gp in self._gps(periods):
            vel = gp.grid_file(method, "cb", dcheck=dcheck)
            if vel.exists():
                fig_name = gp.fig_name(method, "cb")
                plot_vel(vel, self.region, fig_name, eles, self.cptcf)

    def std(self, *, periods=None, eles):
        for gp in self._gps(periods):
            vel = gp.grid_file("tpwt", "vel")
            std = gp.grid_file("tpwt", "std")
            if all([vel.exists(), std.exists()]):
                plot_as(vel, std, self.region, gp.fig_name("tpwt", "as"), eles)

    def diff(self, *, eles, periods=None):
        for gp in self._gps(periods):
            ant = gp.grid_file("ant", "vel")
            tpwt = gp.grid_file("tpwt", "vel")
            if all([ant.exists(), tpwt.exists()]):
                plot_diff(tpwt, ant, self.region, gp.diff_name(), eles)

    def _gps(self, periods):
        pers = periods or self.periods
        return tqdm(gp for gp in self.gps if gp.period in pers)
