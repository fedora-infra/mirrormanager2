-- Exported definition from 2009-04-06T23:25:31
-- Class mirrormanager.model.SiteAdmin
-- Database: sqlite
CREATE TABLE site_admin (
    id INTEGER PRIMARY KEY,
    username TEXT,
    site_id INT CONSTRAINT site_id_exists REFERENCES site(id) 
)
