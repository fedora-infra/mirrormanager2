"""Drop the site_to_site table

Revision ID: b4ec15824475
Revises: 3264c6353b51
Create Date: 2026-11-16 13:05:53.183925

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b4ec15824475"
down_revision = "3264c6353b51"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("site_to_site")


def downgrade():
    op.create_table(
        "site_to_site",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column("password", sa.Text(), nullable=True),
        sa.Column("upstream_site_id", sa.Integer(), nullable=False),
        sa.Column("downstream_site_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["downstream_site_id"], ["site.id"]),
        sa.ForeignKeyConstraint(["upstream_site_id"], ["site.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("upstream_site_id", "downstream_site_id", name="site_to_site_idx"),
        sa.UniqueConstraint("upstream_site_id", "username", name="site_to_site_username_idx"),
    )
