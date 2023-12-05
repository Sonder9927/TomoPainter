from tomopainter import TomoPainter


def paint():
    pr = TomoPainter()
    # pr.initialize(lab_range=[-45, -150])
    # pr.print_info(span=[60,80,200,250])

    # pr.profiles()
    pr.plot("as", periods=[125, 143])

    # pr.map("area")
    # pr.plot("profiles")


if __name__ == "__main__":
    paint()
