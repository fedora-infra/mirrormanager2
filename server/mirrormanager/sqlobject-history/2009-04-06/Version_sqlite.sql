-- Exported definition from 2009-04-06T23:25:31
-- Class mirrormanager.model.Version
-- Database: sqlite
CREATE TABLE version (
    id INTEGER PRIMARY KEY,
    name TEXT,
    product_id INT CONSTRAINT product_id_exists REFERENCES product(id) ,
    is_test BOOLEAN,
    display BOOLEAN,
    display_name TEXT,
    ordered_mirrorlist BOOLEAN
)
