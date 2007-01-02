-- Exported definition from 2006-11-24T09:58:02
-- Class mirrors.model.Arch
-- Database: postgres
CREATE TABLE arch (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    comment TEXT
)
CREATE TABLE arch_release (
arch_id INT NOT NULL,
release_id INT NOT NULL
)
