-- Exported definition from 2009-10-21T08:14:00
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
