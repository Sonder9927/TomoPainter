from .gmt_make_data import area_clip


def fig_tomos(fig, topo, tomos, frame=None, **kwargs):
    if frame is None:
        frame = "a"
    tomo_param = {"nan_transparent": True}
    # basemap and topo
    fig.basemap(
        region=topo["region"],
        projection=kwargs.get("projection") or _hscale(topo["region"]),
        frame=frame,
    )
    if gra := topo.get("gra"):
        fig.grdimage(
            grid=topo["grd"],
            cmap=topo["cpt"],
            shading=gra,
        )
        tomo_param["shading"] = gra
    # plot tomos
    if kwargs.get("clip"):
        for tomo in tomos:
            tomo["grid"] = area_clip(tomo["grid"], region=topo["region"])
            fig.grdimage(**tomo, **tomo_param)
    else:
        for tomo in tomos:
            fig.grdimage(**tomo, **tomo_param)
    # plot tects and stas
    if (tect := kwargs.get("tect")) is not None:
        fig = fig_tect_and_sta(fig, tect, kwargs.get("sta"))
    # plot lines
    lines = kwargs.get("lines")
    if lines is not None:
        for line in lines:
            fig.plot(data=line, pen=kwargs["line_pen"])
    return fig


def fig_tect_and_sta(fig, tect, sta):
    # stations and China_tectonic
    # lines
    geo_data = ["China_tectonic.dat", "CN-faults.gmt", "find.gmt"]
    fig.coast(shorelines="1/0.5p,black")
    tect_pens = ["1p,black,-", "0.5p,black,-"]
    fig.plot(data=f"data/txt/tects/{geo_data[tect]}", pen=tect_pens[0])
    fig.plot(data="data/txt/tects/small_faults.gmt", pen=tect_pens[1])
    # fig.plot(data="data/txt/tects/small_faults_finding.gmt", pen="red,-")
    if sta is not None:
        fig.plot(data=sta, style="t0.1c", fill="darkblue")
    return fig


def _hscale(region: list) -> str:
    # projection
    x = (region[0] + region[1]) / 2
    y = (region[2] + region[3]) / 2
    return f"m{x}/{y}/0.3i"
