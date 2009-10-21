-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.HostCountryAllowed
-- Database: sqlite
CREATE TABLE host_country_allowed (
    id INTEGER PRIMARY KEY,
    host_id INT CONSTRAINT host_id_exists REFERENCES host(id) ,
    country TEXT NOT NULL
)
