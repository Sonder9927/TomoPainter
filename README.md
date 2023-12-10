# TomoPainter

use pygmt plot tomography in geophysics

package name: `tomo`

class: `TomoPainter`

functions: `make_ppt`

# data structure

4 tables:

- grid(id, x, y)
- model(grid_id, sedthk, rf_moho, mc_misfit, mc_moho, poisson)
- phase(grid_id, method, period, vel, std, dcheck..)
- swave(grid_id, depth, rj_vs, mc_vs)
