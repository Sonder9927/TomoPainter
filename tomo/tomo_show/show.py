from .make_ppt import PptMaker


def make_ppt(ppt_name, figs):
    ppt = PptMaker(pn=ppt_name, fig_root=figs, remake=True)
    ppt.add_area(r"area_figs")
    ppt.add_phase_results(r"phase")
    ppt.add_dispersion_curves(r"dispersion_curves")
    ppt.add_mc_results(r"mc_figs")
    ppt.save()
