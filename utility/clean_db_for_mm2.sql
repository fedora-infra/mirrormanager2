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


-- Add some indexes
CREATE INDEX t_host_site_id_idx ON host (site_id);
CREATE INDEX t_category_product_id_idx ON category (product_id);
CREATE INDEX t_category_topdir_id_idx ON category (topdir_id);
CREATE INDEX t_sitetosite_upstream_site_id_idx ON site_to_site (upstream_site_id);
CREATE INDEX t_sitetosite_downstream_site_id_idx ON site_to_site (downstream_site_id);
CREATE INDEX t_siteadmin_site_id_idx ON site_admin (site_id);
CREATE INDEX t_hostcategory_host_id_idx ON host_category (host_id);
CREATE INDEX t_hostcategory_category_id_idx ON host_category (category_id);
CREATE INDEX t_hostcategorydir_host_category_id_idx ON  host_category_dir (host_category_id);
CREATE INDEX t_hostcategorydir_directory_id_idx ON host_category_dir (directory_id);
CREATE INDEX t_hostcategoryurl_host_category_id_idx ON host_category_url (host_category_id);
CREATE INDEX t_hostaclip_host_id_idx ON host_acl_ip (host_id);
CREATE INDEX t_hostcountryallowed_host_id_idx ON host_country_allowed (host_id);
CREATE INDEX t_hostnetblock_host_id_idx ON host_netblock (host_id);
CREATE INDEX t_hostpeerasn_host_id_idx ON host_peer_asn (host_id);
CREATE INDEX t_hoststats_host_id_idx ON host_stats (host_id);
CREATE INDEX t_version_product_id_idx ON version (product_id);
CREATE INDEX t_repository_category_id_idx ON repository (category_id);
CREATE INDEX t_repositoryversion_id_idx ON repository (version_id);
CREATE INDEX t_repositoryarch_id_idx ON repository (arch_id);
CREATE INDEX t_repositorydirectory_id_idx ON repository (directory_id);
CREATE INDEX t_directoryexclusivehost_host_id_idx ON directory_exclusive_host (host_id);
CREATE INDEX t_directoryexclusivehost_directory_id_idx ON directory_exclusive_host (directory_id);
CREATE INDEX t_hostlocation_host_id_idx ON host_location (host_id);
CREATE INDEX t_hostlocation_location_id_idx ON host_location (location_id);
CREATE INDEX t_filedetailfilegroup_file_detail_id_idx ON file_detail_file_group (file_detail_id);
CREATE INDEX t_filedetailfilegroup_file_group_id_idx ON file_detail_file_group (file_group_id);
CREATE INDEX t_hostcountry_host_id_idx ON host_country (host_id);
CREATE INDEX t_hostcountry_country_id_idx ON host_country (country_id);
