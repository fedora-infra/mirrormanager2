"""Make site.all_sites_can_pull_from_me nullable

Revision ID: 1c33a28970a2
Revises: b4ec15824475
Create Date: 2026-11-16 12:32:48.049689

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1c33a28970a2"
down_revision = "b4ec15824475"
branch_labels = None
depends_on = None


def upgrade():
    # The model no longer has the column, so a new site gets NULL in it. A database created by
    # MirrorManager2 has the column as NOT NULL without a server default, and inserting a site
    # fails there.
    with op.batch_alter_table("site") as batch_op:
        batch_op.alter_column(
            "all_sites_can_pull_from_me", existing_type=sa.Boolean(), nullable=True
        )


def downgrade():
    # A database created from the model of this revision has neither all_sites_can_pull_from_me
    # nor downstream_comments, but the model of the previous revision selects both columns.
    columns = [column["name"] for column in sa.inspect(op.get_bind()).get_columns("site")]
    if "downstream_comments" not in columns:
        op.add_column("site", sa.Column("downstream_comments", sa.Text(), nullable=True))
    if "all_sites_can_pull_from_me" not in columns:
        op.add_column("site", sa.Column("all_sites_can_pull_from_me", sa.Boolean(), nullable=True))
    op.execute(
        "UPDATE site SET all_sites_can_pull_from_me = false "
        "WHERE all_sites_can_pull_from_me IS NULL"
    )
    with op.batch_alter_table("site") as batch_op:
        batch_op.alter_column(
            "all_sites_can_pull_from_me", existing_type=sa.Boolean(), nullable=False
        )
