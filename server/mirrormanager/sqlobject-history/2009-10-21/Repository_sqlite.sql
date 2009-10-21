-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.Repository
-- Database: sqlite
CREATE TABLE repository (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    prefix TEXT,
    category_id INT CONSTRAINT category_id_exists REFERENCES category(id) ,
    version_id INT CONSTRAINT version_id_exists REFERENCES version(id) ,
    arch_id INT CONSTRAINT arch_id_exists REFERENCES arch(id) ,
    directory_id INT CONSTRAINT directory_id_exists REFERENCES directory(id) ,
    disabled BOOLEAN
);
CREATE UNIQUE INDEX repository_idx ON repository (prefix, arch_id)
