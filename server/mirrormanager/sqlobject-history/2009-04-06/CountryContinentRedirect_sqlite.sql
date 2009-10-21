-- Exported definition from 2009-04-06T23:25:30
-- Class mirrormanager.model.CountryContinentRedirect
-- Database: sqlite
CREATE TABLE country_continent_redirect (
    id INTEGER PRIMARY KEY,
    country TEXT NOT NULL UNIQUE,
    continent TEXT NOT NULL
)
