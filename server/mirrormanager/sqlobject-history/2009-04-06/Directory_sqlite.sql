-- Exported definition from 2009-04-06T23:25:30
-- Class mirrormanager.model.Directory
-- Database: sqlite
CREATE TABLE directory (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    files TEXT,
    readable BOOLEAN,
    ctime BIGINT
)
