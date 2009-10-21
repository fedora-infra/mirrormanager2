-- Exported definition from 2009-04-06T23:25:31
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
