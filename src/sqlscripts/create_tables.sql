PRAGMA foreign_keys = ON;
-- grid nodes(id, x, y)
CREATE TABLE grid (
  id INT PRIMARY KEY,
  x FLOAT not null,
  y FLOAT not null
);

-- grid models(grid_id, sed, rf_moho, mc_misfit, mc_moho, poisson)
CREATE TABLE model (
  grid_id INT,
  sedthk FLOAT,
  rf_moho FLOAT,
  mc_misfit FLOAT,
  mc_moho FLOAT,
  lab FLOAT,
  poisson FLOAT,
  FOREIGN KEY (grid_id) REFERENCES grid(id)
);

-- surface wave
-- (grid_id, method(ant/tpwt), period, velocity, standard_deviation, dcheck)
-- write in python because of the lack of colmn names of dcheck.
-- CREATE TABLE phase (
--   -- id INT PRIMARY KEY,
--   grid_id INT,
--   method VARCHAR(4),
--   period INT,
--   vel FLOAT,
--   std FLOAT,
--   dcheck FLOAT,
--   FOREIGN KEY (grid_id) REFERENCES grid(id)
-- );

-- shear wave (grid_id, depth, velocity, group(ant/tpwt))
CREATE TABLE swave (
  -- id INT PRIMARY KEY,
  grid_id INT,
  depth FLOAT,
  rj_vs FLOAT,
  mc_vs FLOAT,
  FOREIGN KEY (grid_id) REFERENCES grid(id)
);
