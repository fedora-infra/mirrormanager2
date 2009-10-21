-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.FileDetail
-- Database: sqlite
CREATE TABLE file_detail (
    id INTEGER PRIMARY KEY,
    directory_id INT NOT NULL CONSTRAINT directory_id_exists REFERENCES directory(id) ,
    filename TEXT NOT NULL,
    timestamp BIGINT,
    size BIGINT,
    sha1 TEXT,
    md5 TEXT,
    sha256 TEXT,
    sha512 TEXT
)
