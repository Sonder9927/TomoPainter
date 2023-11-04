import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import pygmt
from tomo.tomo_paint.gmt import area_clip, lines_generator, tomo_grid


class GridPhv:
    def __init__(self, period, series=None) -> None:
        self.period = int(period)
        self.series = series
        self.grids = Path("data/grids")

    def grid_file(self, method, identifier, dcheck=None) -> Path | None:
        idt = _check_identifier(identifier)
        gsp = self.grids / f"{method}_grids"
        if idt == "cb":
            gsp = gsp / f"dcheck_{dcheck}"
        return gsp / f"{method}_{idt}_{self.period}.grid"

    def fig_name(self, method, identifier: str) -> str:
        idt = _check_identifier(identifier)
        return f"images/{method}_figs/{method}_{idt.lower()}_{self.period}.png"

    def diff_name(self):
        return f"images/diff_figs/diff_{self.period}.png"


class GridVs:
    def __init__(self, hregion, vs_file, ml_file) -> None:
        self.hregion = hregion
        self.vs = pd.read_csv(vs_file)
        self.depths = self.vs["z"].unique().tolist()
        self.ml = pd.read_csv(ml_file)
        self.ddp = Path("temp/depths_data")
        self.linetypes = ["arise", "decline", "xline", "yline"]
        self.profile = Path("data/txt/profile.json")
        self._init_data()

    # project path with two points
    def init_path(self, line, linetype):
        froot = Path(rf"images/mc_figs/profile/{linetype}")
        if not froot.exists():
            froot.mkdir(parents=True)
        [point1, point2] = line
        # calculate the path representing points of the line
        path = pygmt.project(
            center=point1, endpoint=point2, generate="10", unit=True
        )
        path.columns = ["x", "y", "z"]
        # make string like `images/vs_point1-point2`
        points_string = f"{point1[0]}X{point1[1]}-{point2[0]}X{point2[1]}"
        fn = froot / f"vs_{points_string}"

        return path, str(fn)

    def depths_data(self, idt, ave, *, depths=None, dep_filter=None):
        suffix = "_ave" if ave else "_vel"
        depths = [] if depths is None else [-abs(d) for d in depths]
        if dep_filter is not None:
            depths += [dd for dd in self.depths if dep_filter(dd)]
        for dd in depths:
            dep = int(dd)
            grid = self.ddp / f"{idt}{dep}{suffix}.grd"
            if not grid.exists():
                raise FileNotFoundError(f"Not found {grid}")
            fn = rf"images/mc_figs/depth/vs_{-dep}km{suffix}.png"
            yield dd, str(grid), fn

    # pick vs data of grid where is on the path
    def track_vs(self, path, ave=False):
        # init dataframe
        data = pd.DataFrame(columns=["x", "y", "z", "v"])
        # get the set of depths
        for dep, grid, _ in self.depths_data("sf", ave, depths=self.depths):
            res = pygmt.grdtrack(
                points=path, grid=grid, verbose="w", newcolname="track"
            )
            if res is None:
                raise ValueError(r"No result for `grdtrack`.")
            res = res.iloc[:, [0, 1, 3]]
            res["z"] = dep
            res.columns = ["x", "y", "v", "z"]
            data = pd.concat([data, res])

        return data

    # pick moho data of grid where is on the path
    def track_border(self, idt, path: pd.DataFrame):
        temp_grd = r"temp/temp.grd"
        data = self.ml[["x", "y", idt]]
        # tomo_grid_data(data, temp_grd, self.hregion, surface=0.25)
        tomo_grid(data, self.hregion, temp_grd, surface=0.25)
        track: pd.DataFrame = pygmt.grdtrack(
            points=path,
            grid=temp_grd,
            verbose="w",
            newcolname="newz",
            coltypes="g",
        )  # pyright: ignore
        track.columns = ["x", "y", "n", "z"]
        return track[["x", "y", "z"]]

    # create data of per depth
    def _init_data(self):
        # init profile lines into json file
        if not self.profile.exists():
            lls = {"x": [], "y": []}
            for lt in self.linetypes:
                for idt, ll in lines_generator(self.hregion, lt):
                    lls[idt].append(ll)
            with self.profile.open("w", encoding="utf-8") as f:
                json.dump(lls, f)
        # init grid of per depth
        if self.ddp.exists():
            return
        self.ddp.mkdir()
        with ProcessPoolExecutor(max_workers=10) as pool:
            for dep in self.depths:
                df = self.vs[self.vs["z"] == dep]
                df = df[["x", "y", "v"]]
                df.columns = ["x", "y", "z"]
                pool.submit(_depth_grid, df, self.ddp, int(dep), self.hregion)


def _depth_grid(data, ddp: Path, dep, region):
    fn = str(ddp / f"pre{dep}_vel.grd")
    _image_ang_track(fn, data, region)
    # ave data
    df_clip = area_clip(data)
    mean_value = df_clip["z"].mean()
    data["z"] = (data["z"] - mean_value) / mean_value * 100
    fn = str(ddp / f"pre{dep}_ave.grd")
    _image_ang_track(fn, data, region)


def _image_ang_track(fn, data, region):
    # grid for hpanel grdimage
    tomo_grid(data, region, fn.replace("pre", "tomo"))
    # grid surface for track
    ff = fn.replace("pre", "sf")
    pygmt.surface(data=data, region=region, spacing=0.5, outgrid=ff)
    # pygmt.grdsample(grid=ff, region=region, spacing=0.1, outgrid=ff)


def _check_identifier(identifier: str) -> str:
    ids = {"vel", "cb", "std", "as"}
    if (idt := identifier.lower()) not in ids:
        raise KeyError(f"identifier: {identifier}")
    return idt
