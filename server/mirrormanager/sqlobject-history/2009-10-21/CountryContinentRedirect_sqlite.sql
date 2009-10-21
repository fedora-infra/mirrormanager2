-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.CountryContinentRedirect
-- Database: sqlite
CREATE TABLE country_continent_redirect (
    id INTEGER PRIMARY KEY,
    country TEXT NOT NULL UNIQUE,
    continent TEXT NOT NULL
)
