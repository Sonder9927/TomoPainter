from tomopainter import TomoPainter, DataQueryer


def paint():
    with DataQueryer("data/grids.db") as queryer:
        painter = TomoPainter(queryer)
        # pr.initialize(lab_range=[-45, -150])
        # pr.print_info(span=[60,80,200,250])
        # pr.map("area")
        painter.plot(idt="profiles", method="mc", depths=200)
        painter.plot(idt="profiles", method="mc", depths=200, ave=True)
        painter.plot(idt="profiles", method="rj", depths=60)
        painter.plot(idt="profiles", method="rj", depths=60, ave=True)


if __name__ == "__main__":
    paint()
