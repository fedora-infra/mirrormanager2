-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.HostCategoryDir
-- Database: sqlite
CREATE TABLE host_category_dir (
    id INTEGER PRIMARY KEY,
    host_category_id INT CONSTRAINT host_category_id_exists REFERENCES host_category(id) ,
    path TEXT,
    directory_id INT CONSTRAINT directory_id_exists REFERENCES directory(id) ,
    up2date BOOLEAN,
    files TEXT,
    last_crawled TIMESTAMP
);
CREATE UNIQUE INDEX host_category_dir_hcdindex ON host_category_dir (host_category_id, path)
