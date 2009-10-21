-- Exported definition from 2009-04-06T23:25:31
-- Class mirrormanager.model.HostAclIp
-- Database: sqlite
CREATE TABLE host_acl_ip (
    id INTEGER PRIMARY KEY,
    host_id INT CONSTRAINT host_id_exists REFERENCES host(id) ,
    ip TEXT
)
