set shell := ["fish", "-c"]

vi := "lvim"

# default
hello:
    @echo 'Hello, world!'
    @just --list

tree_ignore := "'grids|temp'"

# tree
tree:
  tree -I {{tree_ignore}}

# run python scripts to update figs
up:
  python result_show.py

# rsync mcmc
rsmc:
  rs wuzx@10.16.124.156:disk_01/mcmc/mcmc_merak/mc_figs mc_loop/mc_new
  rs wuzx@10.16.124.156:disk_01/mcmc/mcmc_merak/vs.csv src/txt/vs.csv
  rs wuzx@10.16.124.156:disk_01/mcmc/mcmc_merak/misfit_moho.csv src/txt/misfit_moho.csv

# show figure
show:
  feh images
