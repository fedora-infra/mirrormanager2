-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.SiteAdmin
-- Database: sqlite
CREATE TABLE site_admin (
    id INTEGER PRIMARY KEY,
    username TEXT,
    site_id INT CONSTRAINT site_id_exists REFERENCES site(id) 
)
