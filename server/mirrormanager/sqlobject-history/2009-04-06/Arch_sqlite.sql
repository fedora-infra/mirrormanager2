-- Exported definition from 2009-04-06T23:25:30
-- Class mirrormanager.model.Arch
-- Database: sqlite
CREATE TABLE arch (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    publiclist BOOLEAN,
    primary_arch BOOLEAN
)
