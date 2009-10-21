-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.HostNetblock
-- Database: sqlite
CREATE TABLE host_netblock (
    id INTEGER PRIMARY KEY,
    host_id INT CONSTRAINT host_id_exists REFERENCES host(id) ,
    netblock TEXT
)
