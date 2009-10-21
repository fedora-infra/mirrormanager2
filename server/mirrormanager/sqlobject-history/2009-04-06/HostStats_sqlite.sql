-- Exported definition from 2009-04-06T23:25:31
-- Class mirrormanager.model.HostStats
-- Database: sqlite
CREATE TABLE host_stats (
    id INTEGER PRIMARY KEY,
    host_id INT CONSTRAINT host_id_exists REFERENCES host(id) ,
    timestamp TIMESTAMP,
    type TEXT,
    data TEXT
)
