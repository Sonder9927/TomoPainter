# from .phase import PhasePainter
# from .dispersion import gmt_plot_dispersion_curves
# from .area import gmt_plot_misfit, AreaPainter
# from .s_wave import gmt_plot_vs

# __all__ = [
#     "gmt_plot_dispersion_curves",
#     "gmt_plot_misfit",
#     "gmt_plot_vs",
#     "AreaPainter",
#     "PhasePainter",
# ]
from tomopainter.tomo_paint import TomoPainter
from tomopainter.tomo_show import make_ppt

__all__ = ["TomoPainter", "make_ppt"]
