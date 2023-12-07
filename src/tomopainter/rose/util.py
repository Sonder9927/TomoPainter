from shapely.geometry import Point, LineString


class Region:
    def __init__(self, region, spacing):
        self.begin = Point(region[0], region[2])
        self.end = Point(region[1], region[3])
        self.spacing = spacing

    def change(self, spacing=None):
        spacing = spacing or self.spacing
        self.begin = Point(self.begin.x + spacing, self.begin.y + spacing)
        self.end = Point(self.end.x + spacing, self.end.y + spacing)

    def to_list(self, change: None | float = None):
        x, y = LineString([self.begin, self.end]).xy
        if change is not None:
            x = [x[0] - change, x[1] + change]
            y = [y[0] - change, y[1] + change]
        return x + y
