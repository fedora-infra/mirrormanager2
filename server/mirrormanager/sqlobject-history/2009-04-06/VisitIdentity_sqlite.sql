-- Exported definition from 2009-04-06T23:25:30
-- Class mirrormanager.model.VisitIdentity
-- Database: sqlite
CREATE TABLE visit_identity (
    id INTEGER PRIMARY KEY,
    visit_key VARCHAR (40) NOT NULL UNIQUE,
    user_id INT
)
