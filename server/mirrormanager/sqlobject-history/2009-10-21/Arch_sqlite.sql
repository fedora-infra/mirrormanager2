-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.Arch
-- Database: sqlite
CREATE TABLE arch (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    publiclist BOOLEAN,
    primary_arch BOOLEAN
)
