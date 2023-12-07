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
  poisson FLOAT,
  FOREIGN KEY (grid_id) REFERENCES grid(id)
);

-- surface wave
-- (grid_id, group(ant/tpwt), period, velocity, standard_deviation, checkboard(1.5 & 2))
CREATE TABLE phase (
  -- id INT PRIMARY KEY,
  grid_id INT,
  method VARCHAR(4),
  period INT,
  phase_velocity FLOAT,
  standard_deviation FLOAT,
  "cbeckboard1.5_velocity" FLOAT,
  checkboard2_velocity FLOAT,
  FOREIGN KEY (grid_id) REFERENCES grid(id)
);

-- shear wave (grid_id, depth, velocity, group(ant/tpwt))
CREATE TABLE swave (
  -- id INT PRIMARY KEY,
  grid_id INT,
  method VARCHAR(4),
  depth FLOAT,
  velocity FLOAT,
  FOREIGN KEY (grid_id) REFERENCES grid(id)
);
