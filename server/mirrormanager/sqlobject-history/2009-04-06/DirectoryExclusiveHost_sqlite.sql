-- Exported definition from 2009-04-06T23:25:31
-- Class mirrormanager.model.DirectoryExclusiveHost
-- Database: sqlite
CREATE TABLE directory_exclusive_host (
    id INTEGER PRIMARY KEY,
    directory_id INT CONSTRAINT directory_id_exists REFERENCES directory(id) ,
    host_id INT CONSTRAINT host_id_exists REFERENCES host(id) 
);
CREATE UNIQUE INDEX directory_exclusive_host_idx ON directory_exclusive_host (directory_id, host_id)
