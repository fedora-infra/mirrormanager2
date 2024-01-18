"""access statistics

Revision ID: 8d2832628792
Revises: 920e847c8c36
Create Date: 2024-01-18 15:15:27.425534

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8d2832628792"
down_revision = "920e847c8c36"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "access_stat_category",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_access_stat_category")),
        sa.UniqueConstraint("name", name=op.f("uq_access_stat_category_name")),
    )
    op.create_table(
        "access_stat",
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("percent", sa.Float(), nullable=True),
        sa.Column("requests", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["access_stat_category.id"],
            name=op.f("fk_access_stat_category_id_access_stat_category"),
        ),
        sa.PrimaryKeyConstraint("category_id", "date", "name", name=op.f("pk_access_stat")),
    )
    op.create_index(
        op.f("ix_access_stat_category_id"), "access_stat", ["category_id"], unique=False
    )
    op.create_index(op.f("ix_access_stat_date"), "access_stat", ["date"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_access_stat_date"), table_name="access_stat")
    op.drop_index(op.f("ix_access_stat_category_id"), table_name="access_stat")
    op.drop_table("access_stat")
    op.drop_table("access_stat_category")
