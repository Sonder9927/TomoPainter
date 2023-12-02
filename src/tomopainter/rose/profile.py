import json

import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiPoint


def idt_profiles(jsonfile, idt=True):
    """
    jsonfile: input file
    return: lines with idt or not
    """
    with open(jsonfile) as f:
        profiles = json.load(f)
    idt_lines = profiles.items()
    if idt:
        return idt_lines
    lines = []
    for _, lls in idt_lines:
        lines.extend(iter(lls))
    return np.array(lines)


def init_profiles(region, outfile):
    linetypes = ["arise", "decline", "xline", "yline"]
    lls = {"x": [], "y": []}
    for lt in linetypes:
        for idt, ll in lines_generator(region, lt):
            lls[idt].append(ll)
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(lls, f)


def lines_generator(region, linetype):
    xx = region[:2]
    yy = region[-2:]
    d = 0.5
    df = pd.read_csv("data/txt/area_hull.csv")
    points = list(zip(df["x"], df["y"]))
    hull = MultiPoint(points).convex_hull
    hlines = [
        LineString([(xx[0], y), (xx[1], y)])
        for y in np.arange(yy[0] + d, yy[1], d)
    ]
    vlines = [
        LineString([(x, yy[0]), (x, yy[1])])
        for x in np.arange(xx[0] + 1, xx[1], d)
    ]
    if linetype == "decline":
        l0 = [[116, 34.5], [122, 32.5]]
        yield from _incline(hull, l0, xx, yy, "x", [3, 4])
    elif linetype == "arise":
        l0 = [[116, 30], [119.5, 34]]
        yield from _incline(hull, l0, xx[::-1], yy, "y", [6, 8])
    elif linetype == "xline":
        for ll in hlines:
            interl = hull.intersection(ll)
            yield "x", _round_line(interl)
    elif linetype == "yline":
        for ll in vlines:
            interl = hull.intersection(ll)
            yield "y", _round_line(interl)
    else:
        raise NotImplementedError


def _incline(hull, l0, xx, yy, idt, bias):
    dd = 0.5
    k = (l0[0][1] - l0[1][1]) / (l0[0][0] - l0[1][0])
    b_min = yy[0] - k * xx[0]
    b_max = yy[1] - k * xx[1]

    for b in np.arange(b_min + dd * bias[0], b_max - dd * bias[1], dd):

        def point(x):
            return (x, k * x + b)

        line = LineString([point(xx[0]), point(xx[1])])
        inter_line = hull.intersection(line)
        yield idt, _round_line(inter_line)
        # xxxx = sorted(xx + [(t - b) / k for t in yy])

        # def round_point(x):
        #     return [round(x, 1), round(k * x + b, 1)]

        # ll = [round_point(xxxx[1]), round_point(xxxx[2])]
        # yield idt, ll


def _round_line(line: LineString) -> list[list]:
    import math

    coords = list(line.coords)
    if len(coords) != 2:
        raise ValueError(f"{line} is out of region")

    [p1, p2] = sorted([[round(c, 2) for c in p] for p in coords])
    p1[0] = math.ceil(p1[0] * 10) / 10
    p2[0] = math.floor(p2[0] * 10) / 10
    if p1[1] <= p2[1]:
        p1[1] = math.ceil(p1[1] * 10) / 10
        p2[1] = math.floor(p2[1] * 10) / 10
    else:
        p1[1] = math.floor(p1[1] * 10) / 10
        p2[1] = math.ceil(p2[1] * 10) / 10
    return [p1, p2]
