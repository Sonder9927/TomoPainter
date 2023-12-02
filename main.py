from tomopainter import TomoPainter, make_ppt


def paint():
    pr = TomoPainter()
    # pr.initialize(lab_range=[-45, -150])
    # pr.print_info(span=[60,80,200,250])

    # pr.profiles()

    pr.map("model")
    # pr.dispersion()


if __name__ == "__main__":
    paint()
    # make_ppt()
