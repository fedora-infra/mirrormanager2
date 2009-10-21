-- Exported definition from 2009-10-21T08:14:00
-- Class mirrormanager.model.VisitIdentity
-- Database: sqlite
CREATE TABLE visit_identity (
    id INTEGER PRIMARY KEY,
    visit_key VARCHAR (40) NOT NULL UNIQUE,
    user_id INT
)
