-- Exported definition from 2009-04-06T23:25:30
-- Class mirrormanager.model.Visit
-- Database: sqlite
CREATE TABLE visit (
    id INTEGER PRIMARY KEY,
    visit_key VARCHAR (40) NOT NULL UNIQUE,
    created TIMESTAMP,
    expiry TIMESTAMP
)
