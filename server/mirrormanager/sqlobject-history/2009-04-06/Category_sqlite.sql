-- Exported definition from 2009-04-06T23:25:31
-- Class mirrormanager.model.Category
-- Database: sqlite
CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    product_id INT CONSTRAINT product_id_exists REFERENCES product(id) ,
    canonicalhost TEXT,
    topdir_id INT CONSTRAINT topdir_id_exists REFERENCES directory(id) ,
    publiclist BOOLEAN
);
CREATE TABLE category_directory (
category_id INT NOT NULL,
directory_id INT NOT NULL
)
