-- Exported definition from 2009-04-06T23:25:31
-- Class mirrormanager.model.HostCategory
-- Database: sqlite
CREATE TABLE host_category (
    id INTEGER PRIMARY KEY,
    host_id INT CONSTRAINT host_id_exists REFERENCES host(id) ,
    category_id INT CONSTRAINT category_id_exists REFERENCES category(id) ,
    admin_active BOOLEAN,
    user_active BOOLEAN,
    upstream TEXT,
    always_up2date BOOLEAN
);
CREATE UNIQUE INDEX host_category_hcindex ON host_category (host_id, category_id)
