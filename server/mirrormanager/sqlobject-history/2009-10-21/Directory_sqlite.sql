-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.Directory
-- Database: sqlite
CREATE TABLE directory (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    files TEXT,
    readable BOOLEAN,
    ctime BIGINT
)
