CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS btree_gist;  -- lets the GiST exclusion constraint compare text ids with =

CREATE TABLE fragment (
    id        text      NOT NULL,  -- version-independent path, e.g. oz/par_2239/odst_1
    law       text      NOT NULL,  -- oz, nv308, z67, osr
    par       text,
    odst      text,
    pism      text,
    citation  text,                -- "§ 2239 odst. 1" as stored by e-Sbírka
    valid     daterange NOT NULL,  -- [from, to); open upper bound = still in force
    text      text      NOT NULL,
    lemmas    text,
    embedding vector(1024),
    EXCLUDE USING gist (id WITH =, valid WITH &&)  -- no two versions of one fragment may overlap
);