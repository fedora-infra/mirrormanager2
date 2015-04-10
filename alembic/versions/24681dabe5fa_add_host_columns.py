"""add_host_columns

Revision ID: 24681dabe5fa
Revises: None
Create Date: 2015-04-09 11:06:47.978441

"""

# revision identifiers, used by Alembic.
revision = '24681dabe5fa'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('host', sa.Column('crawl_failures', sa.Integer))
    op.add_column('host', sa.Column('disable_reason', sa.Text()))
    op.add_column('host', sa.Column('push_ssh_private_key', sa.Text()))
    op.add_column('host', sa.Column('push_ssh_host', sa.Text()))
    op.add_column('host', sa.Column('push_ssh_command', sa.Text()))
    op.add_column('host', sa.Column('last_crawls', sa.PickleType()))

def downgrade():
     op.drop_column('host', 'crawl_failures')
     op.drop_column('host', 'disable_reason')
     op.drop_column('host', 'push_ssh_private_key')
     op.drop_column('host', 'push_ssh_host')
     op.drop_column('host', 'push_ssh_command')
     op.drop_column('host', 'last_crawls')
