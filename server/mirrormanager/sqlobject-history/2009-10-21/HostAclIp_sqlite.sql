-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.HostAclIp
-- Database: sqlite
CREATE TABLE host_acl_ip (
    id INTEGER PRIMARY KEY,
    host_id INT CONSTRAINT host_id_exists REFERENCES host(id) ,
    ip TEXT
)
