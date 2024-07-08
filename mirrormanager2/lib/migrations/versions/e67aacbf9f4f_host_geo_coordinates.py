"""Host geo coordinates

Revision ID: e67aacbf9f4f
Revises: b1f02d039900
Create Date: 2024-07-08 12:08:40.774361

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e67aacbf9f4f"
down_revision = "b1f02d039900"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("host", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("host", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade():
    op.drop_column("host", "longitude")
    op.drop_column("host", "latitude")
