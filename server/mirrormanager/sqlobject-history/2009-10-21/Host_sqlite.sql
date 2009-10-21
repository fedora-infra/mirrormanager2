-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.Host
-- Database: sqlite
CREATE TABLE host (
    id INTEGER PRIMARY KEY,
    name TEXT,
    site_id INT CONSTRAINT site_id_exists REFERENCES site(id) ,
    robot_email TEXT,
    admin_active BOOLEAN,
    user_active BOOLEAN,
    country TEXT,
    bandwidth TEXT,
    bandwidth_int INT,
    comment TEXT,
    config TEXT,
    last_checked_in TIMESTAMP,
    last_crawled TIMESTAMP,
    private BOOLEAN,
    internet2 BOOLEAN,
    internet2_clients BOOLEAN,
    asn INT,
    asn_clients BOOLEAN
);
CREATE UNIQUE INDEX host_idx ON host (site_id, name)
