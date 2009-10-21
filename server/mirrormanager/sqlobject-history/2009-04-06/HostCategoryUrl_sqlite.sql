-- Exported definition from 2009-04-06T23:25:31
-- Class mirrormanager.model.HostCategoryUrl
-- Database: sqlite
CREATE TABLE host_category_url (
    id INTEGER PRIMARY KEY,
    host_category_id INT CONSTRAINT host_category_id_exists REFERENCES host_category(id) ,
    url TEXT NOT NULL UNIQUE,
    private BOOLEAN
)
