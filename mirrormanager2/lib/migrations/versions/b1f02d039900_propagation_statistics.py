"""propagation statistics

Revision ID: b1f02d039900
Revises: 8d2832628792
Create Date: 2024-01-18 16:07:00.203690

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b1f02d039900"
down_revision = "8d2832628792"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "propagation_stat",
        sa.Column("repository_id", sa.Integer(), nullable=True),
        sa.Column("datetime", sa.DateTime(), nullable=False),
        sa.Column("same_day", sa.Integer(), nullable=True),
        sa.Column("one_day", sa.Integer(), nullable=True),
        sa.Column("two_day", sa.Integer(), nullable=True),
        sa.Column("older", sa.Integer(), nullable=True),
        sa.Column("no_info", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repository.id"],
            name=op.f("fk_propagation_stat_repository_id_repository"),
        ),
        sa.PrimaryKeyConstraint("repository_id", "datetime", name=op.f("pk_propagation_stat")),
    )
    op.create_index(
        op.f("ix_propagation_stat_date"), "propagation_stat", ["datetime"], unique=False
    )
    op.create_index(
        op.f("ix_propagation_stat_repository_id"),
        "propagation_stat",
        ["repository_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_propagation_stat_repository_id"), table_name="propagation_stat")
    op.drop_index(op.f("ix_propagation_stat_date"), table_name="propagation_stat")
    op.drop_table("propagation_stat")
