-- SQL Script to update the DB schema from MirrorManager1 to MirrorManager2

-- Drop tables that we no longer use
DROP TABLE "group_permission";
DROP TABLE "permission";
DROP TABLE "tg_visit_identity";
DROP TABLE "visit_identity";
DROP TABLE "country_host";  -- Duplicates of host_country

-- Either drop or rename/adjust (see below)
DROP TABLE "user_group";
DROP TABLE "tg_group";
DROP TABLE "tg_user";
DROP TABLE "visit";


-- -- If you fear there is some data in these table this will rename and
-- -- adjust them.  However, in development at the MM2 FAD we have just been
-- deleting and recreating them.. so, commenting this out.
-- 
-- ALTER TABLE "user_group" RENAME TO "mm_user_group";
-- ALTER TABLE "tg_group" RENAME TO "mm_group";
-- 
-- ALTER TABLE "tg_user" RENAME TO "mm_user";
-- ALTER TABLE "mm_user" ADD COLUMN token varchar(50);
-- ALTER TABLE "mm_user" ADD COLUMN updated_on timestamp without time zone;
-- 
-- ALTER TABLE "visit" RENAME TO "mm_user_visit";
-- ALTER TABLE "mm_user_visit" ADD COLUMN user_id integer;
-- ALTER TABLE ONLY "mm_user_visit"
--     ADD CONSTRAINT user_id_exists FOREIGN KEY (user_id) REFERENCES mm_user(id);


-- Add some indexes
CREATE INDEX t_repository_category_id_idx ON repository (category_id);
CREATE INDEX t_repositoryversion_id_idx ON repository (version_id);
CREATE INDEX t_repositoryarch_id_idx ON repository (arch_id);
CREATE INDEX t_repositorydirectory_id_idx ON repository (directory_id);

CREATE INDEX t_hostcategory_host_id_idx ON host_category (host_id);
CREATE INDEX t_hostcategory_category_id_idx ON host_category (category_id);
