-- Exported definition from 2009-04-06T23:25:30
-- Class mirrormanager.model.SiteToSite
-- Database: sqlite
CREATE TABLE site_to_site (
    id INTEGER PRIMARY KEY,
    upstream_site_id INT CONSTRAINT upstream_site_id_exists REFERENCES site(id) ,
    downstream_site_id INT CONSTRAINT downstream_site_id_exists REFERENCES site(id) 
);
CREATE UNIQUE INDEX site_to_site_idx ON site_to_site (upstream_site_id, downstream_site_id)
