"""add admin only category

Revision ID: 920e847c8c36
Revises: 24681dabe5fa
Create Date: 2021-07-12 18:47:07.433176

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "920e847c8c36"
down_revision = "24681dabe5fa"


def upgrade():
    op.add_column("category", sa.Column("admin_only", sa.Boolean(), default=False))


def downgrade():
    op.drop_column("category", "admin_only")
