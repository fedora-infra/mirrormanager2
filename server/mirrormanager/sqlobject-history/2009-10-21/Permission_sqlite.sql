-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.Permission
-- Database: sqlite
CREATE TABLE permission (
    id INTEGER PRIMARY KEY,
    permission_name VARCHAR (16) NOT NULL UNIQUE,
    description VARCHAR (255)
)
