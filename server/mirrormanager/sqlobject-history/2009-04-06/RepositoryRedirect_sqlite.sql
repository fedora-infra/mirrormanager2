-- Exported definition from 2009-04-06T23:25:30
-- Class mirrormanager.model.RepositoryRedirect
-- Database: sqlite
CREATE TABLE repository_redirect (
    id INTEGER PRIMARY KEY,
    from_repo TEXT NOT NULL UNIQUE,
    to_repo TEXT
);
CREATE UNIQUE INDEX repository_redirect_idx ON repository_redirect (from_repo, to_repo)
