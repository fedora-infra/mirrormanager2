-- SQL Script to update the DB schema from MirrorManager1 to MirrorManager2

-- Drop tables that we no longer use
DROP TABLE "group_permission";
DROP TABLE "permission";
DROP TABLE "tg_visit_identity";
DROP TABLE "visit_identity";

-- Either drop or rename/adjust (see below)
DROP TABLE "user_group";
DROP TABLE "tg_group";
DROP TABLE "tg_user";
DROP TABLE "visit";


-- If you fear there is some data in these table this will rename and
-- adjust them

RENAME TABLE "user_group" TO "mm_user_group";
RENAME TABLE "tg_group" TO "mm_group";

RENAME TABLE "tg_user" TO "mm_user";
ALTER TABLE "mm_user" ADD COLUMN token varchar(50);
ALTER TABLE "mm_user" ADD COLUMN updated_on timestamp without time zone

RENAME TABLE "visit" TO "mm_user_visit";
ALTER TABLE "mm_user_visit" ADD COLUMN user_id integer;
ALTER TABLE ONLY "mm_user_visit"
    ADD CONSTRAINT user_id_exists FOREIGN KEY (user_id) REFERENCES mm_user(id);
