DROP DATABASE IF EXISTS metal_songs_db;
CREATE DATABASE metal_songs_db;
USE metal_songs_db;


CREATE TABLE Bands (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    subgenre TEXT
);

CREATE TABLE Albums (
    id INTEGER PRIMARY KEY,
    band_id INTEGER,
    name TEXT NOT NULL,
    release_year INTEGER,
    FOREIGN KEY (band_id) REFERENCES Bands(id)
);






