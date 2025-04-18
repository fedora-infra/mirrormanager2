"""Indexes

Revision ID: 3264c6353b51
Revises: e67aacbf9f4f
Create Date: 2025-04-18 15:01:59.383709

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "3264c6353b51"
down_revision = "e67aacbf9f4f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f("ix_access_stat_requests"), "access_stat", ["requests"], unique=False)
    op.create_index(op.f("ix_file_detail_timestamp"), "file_detail", ["timestamp"], unique=False)
    op.create_index(op.f("ix_host_admin_active"), "host", ["admin_active"], unique=False)
    op.create_index(op.f("ix_host_country"), "host", ["country"], unique=False)
    op.create_index(
        op.f("ix_host_last_crawl_duration"), "host", ["last_crawl_duration"], unique=False
    )
    op.create_index(op.f("ix_host_name"), "host", ["name"], unique=False)
    op.create_index(op.f("ix_host_private"), "host", ["private"], unique=False)
    op.create_index(op.f("ix_host_user_active"), "host", ["user_active"], unique=False)
    op.create_index(op.f("ix_repository_prefix"), "repository", ["prefix"], unique=False)
    op.create_index(op.f("ix_site_admin_active"), "site", ["admin_active"], unique=False)
    op.create_index(op.f("ix_site_created_at"), "site", ["created_at"], unique=False)
    op.create_index(op.f("ix_site_name"), "site", ["name"], unique=False)
    op.create_index(op.f("ix_site_private"), "site", ["private"], unique=False)
    op.create_index(op.f("ix_site_user_active"), "site", ["user_active"], unique=False)
    op.create_index(
        op.f("ix_host_category_url_private"), "host_category_url", ["private"], unique=False
    )
    op.create_index(
        op.f("ix_host_category_dir_up2date"), "host_category_dir", ["up2date"], unique=False
    )
    op.create_index(op.f("ix_directory_readable"), "directory", ["readable"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_directory_readable"), table_name="directory")
    op.drop_index(op.f("ix_host_category_dir_up2date"), table_name="host_category_dir")
    op.drop_index(op.f("ix_host_category_url_private"), table_name="host_category_url")
    op.drop_index(op.f("ix_site_user_active"), table_name="site")
    op.drop_index(op.f("ix_site_private"), table_name="site")
    op.drop_index(op.f("ix_site_name"), table_name="site")
    op.drop_index(op.f("ix_site_created_at"), table_name="site")
    op.drop_index(op.f("ix_site_admin_active"), table_name="site")
    op.drop_index(op.f("ix_repository_prefix"), table_name="repository")
    op.drop_index(op.f("ix_host_user_active"), table_name="host")
    op.drop_index(op.f("ix_host_private"), table_name="host")
    op.drop_index(op.f("ix_host_name"), table_name="host")
    op.drop_index(op.f("ix_host_last_crawl_duration"), table_name="host")
    op.drop_index(op.f("ix_host_country"), table_name="host")
    op.drop_index(op.f("ix_host_admin_active"), table_name="host")
    op.drop_index(op.f("ix_file_detail_timestamp"), table_name="file_detail")
    op.drop_index(op.f("ix_access_stat_requests"), table_name="access_stat")
