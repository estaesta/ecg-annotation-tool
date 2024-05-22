DROP TABLE IF EXISTS ecg_record;
DROP TABLE IF EXISTS annotation;

CREATE TABLE ecg_record (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  record_name TEXT UNIQUE NOT NULL
);

CREATE TABLE annotation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ecg_record_id INTEGER NOT NULL,
  r_peak_index INTEGER NOT NULL,
  label TEXT,
  FOREIGN KEY (ecg_record_id) REFERENCES ecg_record (id)
);
