-- Exported definition from 2009-04-06T23:25:30
-- Class mirrormanager.model.Site
-- Database: sqlite
CREATE TABLE site (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    password TEXT,
    org_url TEXT,
    private BOOLEAN,
    admin_active BOOLEAN,
    user_active BOOLEAN,
    created_at TIMESTAMP,
    created_by TEXT,
    all_sites_can_pull_from_me BOOLEAN,
    downstream_comments TEXT
)
