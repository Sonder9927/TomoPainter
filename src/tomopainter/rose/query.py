# import pandas as pd
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


class DataQueryer:
    def __init__(self, dbfile) -> None:
        self.dbf = Path(dbfile)
        self.scripts = Path("src/sqlscripts")
        self.conn = sqlite3.connect(self.dbf)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()

    def init_database(self, data_dir, region, spacing=0.5) -> None:
        """initilize data by SQL"""
        if self.dbf.exists():
            self.dbf.unlink()
        data = Path(data_dir)
        # re-connent
        self.conn = sqlite3.connect(self.dbf)
        _conn_write_data(self.conn, data, region, spacing, self.scripts)

    def query(
        self,
        table: str,
        *,
        usecols: None | list[str] = None,
        avecols: None | list[str] = None,
        where: None | str = None,
    ) -> pd.DataFrame:
        cols = "*" if usecols is None else f"x,y,{','.join(usecols)}"
        sql_cmd = f"""SELECT {cols}\nFROM {table}\n"""
        if where is not None:
            sql_cmd += "WHERE {where}\n"
        df = pd.read_sql(sql_cmd, self.conn)
        if avecols is not None:
            for col in avecols:
                avg = df[col].mean()
                df[col] = (df[col] - avg) / avg * 100
        return df

    def test_query(self, table):
        return pd.read_sql(f"select *\nfrom {table}", self.conn)


def _conn_write_data(conn, data, region, spacing, scripts):
    # create tables and set on foreign key
    with open(scripts / "create_tables.sql", "rt") as f:
        create_tables = f.read()
    conn.executescript(create_tables)

    # write main table `grids(id,x,y)`
    args = {"con": conn, "index": False, "if_exists": "append"}
    grid_df = _grid_df(region, spacing)
    grid_df.to_sql("grid", **args)
    # write subtable `model(id,sed,rf_moho,mc_moho)`
    _model_df(data, grid_df).to_sql("model", **args)
    _phase_df(data, grid_df).to_sql("phase", **args)
    _swave_df(data / "vs.csv", grid_df).to_sql("swave", **args)


def _grid_df(region, spacing) -> pd.DataFrame:
    nodes = [
        [x, y]
        for x in np.arange(region[0], region[1] + spacing, spacing)
        for y in np.arange(region[2], region[3] + spacing, spacing)
    ]
    grid_df = pd.DataFrame(data=nodes, columns=["x", "y"])
    grid_df["id"] = range(len(nodes))
    return grid_df


def _model_df(gdir: Path, gdf) -> pd.DataFrame:
    from tomopainter.tomo_paint.gmt import tomo_grid

    rgn = [gdf["x"].min(), gdf["x"].max(), gdf["y"].min(), gdf["y"].max()]
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
    model_df.to_csv("model.csv")
    return model_df


def _model_df_test(gdir: Path, gdf) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "grid_id": [0, 1],
            "sedthk": [1, 1],
            "rf_moho": [34.1, 35.2],
            "poisson": [1.5, 1.7],
            "mc_misfit": [0.2, 0.52],
            "mc_moho": [34, 35],
        }
    )


def _phase_df(gdir: Path, gdf) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "grid_id": [0, 1],
            "period": [20, 25],
            "method": ["tpwt", "ant"],
            "phase_velocity": [3.4, 3.5],
            "standard_deviation": [3.3, 3.2],
            "cbeckboard1.5_velocity": [3.4, 3.4],
            "checkboard2_velocity": [3.4, 3.41],
        }
    )


def _swave_df(gdir: Path, gdf) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "grid_id": [0, 1],
            "depth": [20, 25],
            "velocity": [3.4, 3.5],
            "method": ["tpwt", "ant"],
        }
    )


def xyz_ave(df):
    avg = df["z"].mean()
    df["z"] = (df["z"] - avg) / avg * 100
    return df
