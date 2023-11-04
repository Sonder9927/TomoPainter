from tomo import TomoPainter, make_ppt


def paint():
    pr = TomoPainter()
    # pr.initialize(lab_range=[-50, -150])
    # depths = list(range(10, 210, 10))
    # pr.mcmc(depths=[10])
    # pr.mcmc(profile=True)
    # pr.phase("vel", periods=[20])
    # pr.area("sites")
    pr.phase("cb", "tpwt", dcheck=1.5, periods=[90, 100, 111, 125, 143])
    # pr.dispersion()


if __name__ == "__main__":
    paint()
    # make_ppt()
