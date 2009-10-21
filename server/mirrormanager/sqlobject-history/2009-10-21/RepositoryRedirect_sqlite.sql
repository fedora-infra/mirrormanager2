-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.RepositoryRedirect
-- Database: sqlite
CREATE TABLE repository_redirect (
    id INTEGER PRIMARY KEY,
    from_repo TEXT NOT NULL UNIQUE,
    to_repo TEXT
);
CREATE UNIQUE INDEX repository_redirect_idx ON repository_redirect (from_repo, to_repo)
