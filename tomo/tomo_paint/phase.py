import json

from tqdm import tqdm

from .gmt import plot_as, plot_diff, plot_vel


class PhasePainter:
    def __init__(self, region, ps_file) -> None:
        from tomo.rose import GridPhv

        self.region = region
        with open(ps_file) as f:
            per_se_pairs = json.load(f)
        self.periods = [int(i) for i in per_se_pairs.keys()]
        self.gps: list[GridPhv] = [
            GridPhv(p, s) for p, s in per_se_pairs.items()
        ]

    def vel(self, method, idt, *, periods=None, dcheck=2.0):
        for gp in self._gps(periods):
            if idt == "vel":
                vel = gp.grid_file(method, idt)
                if vel.exists():
                    cpt = {"series": gp.series}
                    plot_vel(vel, self.region, gp.fig_name(method, idt), cpt)
            elif idt == "cb":
                vel = gp.grid_file(method, idt, dcheck=dcheck)
                if vel.exists():
                    plot_vel(vel, self.region, gp.fig_name(method, idt))
            else:
                raise ValueError("choose `vel` or `cb` for idt")

    def std(self, periods=None):
        for gp in self._gps(periods):
            vel = gp.grid_file("tpwt", "vel")
            std = gp.grid_file("tpwt", "std")
            if all([vel.exists(), std.exists()]):
                plot_as(vel, std, self.region, gp.fig_name("tpwt", "as"))

    def diff(self, periods=None):
        for gp in self._gps(periods):
            ant = gp.grid_file("ant", "vel")
            tpwt = gp.grid_file("tpwt", "vel")
            if all([ant.exists(), tpwt.exists()]):
                plot_diff(tpwt, ant, self.region, gp.diff_name())

    def _gps(self, periods):
        pers = periods or self.periods
        return tqdm(gp for gp in self.gps if gp.period in pers)
