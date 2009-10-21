-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.Visit
-- Database: sqlite
CREATE TABLE visit (
    id INTEGER PRIMARY KEY,
    visit_key VARCHAR (40) NOT NULL UNIQUE,
    created TIMESTAMP,
    expiry TIMESTAMP
)
