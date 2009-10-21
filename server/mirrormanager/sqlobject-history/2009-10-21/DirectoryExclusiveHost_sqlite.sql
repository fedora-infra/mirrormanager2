-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.DirectoryExclusiveHost
-- Database: sqlite
CREATE TABLE directory_exclusive_host (
    id INTEGER PRIMARY KEY,
    directory_id INT CONSTRAINT directory_id_exists REFERENCES directory(id) ,
    host_id INT CONSTRAINT host_id_exists REFERENCES host(id) 
);
CREATE UNIQUE INDEX directory_exclusive_host_idx ON directory_exclusive_host (directory_id, host_id)
