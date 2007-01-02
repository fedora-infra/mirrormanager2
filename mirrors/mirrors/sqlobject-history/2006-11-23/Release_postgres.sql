-- Exported definition from 2006-11-23T15:44:17
-- Class mirrors.model.Release
-- Database: postgres
CREATE TABLE release (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    comment TEXT
)
