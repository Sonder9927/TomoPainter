from pathlib import Path

from icecream import ic
import pandas as pd

from tomopainter.tomo_paint.gmt import tomo_grid
from tomopainter.rose import DataQueryer


def read_db():
    with DataQueryer("data/grids.db") as sr:
        # pers = sr.periods
        # ic(pers)
        # deps = sr.depths
        # ic(len(deps["rj"]), len(deps["mc"]))
        # df = sr.query("model")
        # ic(df.head())

        df1 = sr.query("model", usecols=["rf_moho"])
        df2 = sr.query("model", usecols=["poisson"])
        ic(df1.head())
        ic(df2.head())
        df1 = sr.query("model", usecols=["rf_moho"], ave=True)
        df2 = sr.query("model", usecols=["poisson"], ave=True)
        ic(df1.head())
        ic(df2.head())
        # df = sr.swave("mc_vs", depth=20)
        # ic(df.tail())
        # l2 = len(df)
        # ic(l1, l2, l1 / l2)

        # df = sr.phase("tpwt", 10, "vel")
        # ic(df.head())
        # ic(sr.depths)
        # df = sr.query("swave", usecols=["mc_vs"])
        # ic(df.head())
        # df = sr.query("swave", usecols=["mc_vs"], ave=True)
        # ic(df.head())
        # df2 = sr.query("swave", usecols=["mc_vs", "rj_vs"])
        # ic(df2.head())
        # print(sr.names("swave"))


def test_swave_df(gdir, gdf):
    swave_df = None
    for vsf in gdir.glob("*vs.csv"):
        df = pd.read_csv(vsf)
        df = df.merge(gdf, on=["x", "y"], how="left")
        df["depth"] = abs(df["depth"])
        df = df.drop(columns=["x", "y"])
        df.rename(
            columns={"id": "grid_id", "velocity": vsf.stem}, inplace=True
        )
        swave_df = (
            df
            if swave_df is None
            else swave_df.merge(df, on=["grid_id", "depth"], how="outer")
        )
    if swave_df is not None:
        swave_df.sort_values(by=["grid_id", "depth"], inplace=True)
    return swave_df


def test_phase_df(gdir, gdf) -> None | pd.DataFrame:
    phase_df = None
    for mdir in gdir.glob("*/"):
        # data of per method
        method = mdir.name
        dfs = {}
        for gf in mdir.rglob("*.grid"):
            [mtd, idt, period] = gf.stem.split("_")
            if mtd != method:
                raise FileNotFoundError(f"In {method} dir find {mtd}_*.")
            df = pd.read_csv(
                gf, header=None, delim_whitespace=True, names=["x", "y", idt]
            )
            df = gdf.merge(df, on=["x", "y"], how="left")
            df["period"] = period
            df = df[["id", "period", idt]]
            dfs[idt] = pd.concat([dfs[idt], df]) if idt in dfs else df

        # merge all idt dfs of the method
        method_df = None
        for df in dfs.values():
            method_df = (
                df
                if method_df is None
                else method_df.merge(df, on=["id", "period"], how="outer")
            )
        if method_df is None:
            continue
        method_df["method"] = method
        method_df.rename(columns={"id": "grid_id"}, inplace=True)
        # concat all method dfs
        phase_df = (
            method_df if phase_df is None else pd.concat([phase_df, method_df])
        )
    if phase_df is not None:
        phase_df.sort_values(by=["method", "period", "grid_id"], inplace=True)
    return phase_df


def test_model_df(gdf, rgn) -> pd.DataFrame:
    gdir = Path("data/grids")
    # collect data
    # sed data
    sed = pd.read_csv(gdir / "sedthk.xyz", delim_whitespace=True, header=None)
    sed = tomo_grid(sed, rgn).clip(lower=0)

    # receive function moho
    rf = pd.read_csv(
        gdir / "rf_moho.lst",
        delim_whitespace=True,
        usecols=[0, 1, 2],
        header=None,
    )
    rf.iloc[:, 0], rf.iloc[:, 1] = rf.iloc[:, 1].copy(), rf.iloc[:, 0].copy()
    rf = tomo_grid(rf, rgn)

    # merge poisson
    po = pd.read_csv(
        gdir / "input_vpvs.lst", delim_whitespace=True, header=None
    )
    po = tomo_grid(rf, rgn)

    # merge mcmc misfit & moho
    mc = pd.read_csv(gdir / "mcmc_misfit_moho.csv")

    # merge data
    model_df = gdf
    position = ["x", "y"]
    for df in (sed, rf, po, mc):
        model_df = model_df.merge(df, on=position, how="left")
    model_df = model_df.drop(columns=position)
    # rename column names
    model_df.columns = [
        "grid_id",
        "sedthk",
        "rf_moho",
        "poisson",
        "mc_misfit",
        "mc_moho",
    ]
    return model_df


def test_df(region):
    with DataQueryer("data/grids.db") as sr:
        grid = sr.query("grid")
    gdir = Path("data/grids")
    df = test_phase_df(gdir, grid)
    ic(df)


def write_db(region):
    with DataQueryer("data/grids.db") as sr:
        sr.init_database("data/grids", region=region)
        # ic(sr.depths)


if __name__ == "__main__":
    region = [115.5, 122.5, 27, 35]
    # write_db(region)
    read_db()
    # test_df(region)
