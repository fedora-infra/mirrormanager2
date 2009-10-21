-- Exported definition from 2009-04-06T23:25:31
-- Class mirrormanager.model.HostCountryAllowed
-- Database: sqlite
CREATE TABLE host_country_allowed (
    id INTEGER PRIMARY KEY,
    host_id INT CONSTRAINT host_id_exists REFERENCES host(id) ,
    country TEXT NOT NULL
)
