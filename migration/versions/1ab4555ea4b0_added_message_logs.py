"""added message logs

Revision ID: 1ab4555ea4b0
Revises: 2cbd62b3f1fb
Create Date: 2013-02-28 12:56:31.477216

"""

# revision identifiers, used by Alembic.
revision = '1ab4555ea4b0'
down_revision = '2cbd62b3f1fb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('message_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(timezone=True), nullable=False, index=True),
    sa.Column('updated', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.Integer(), nullable=False, index=True),
    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
    sa.Column('message_id', sa.Integer(), nullable=False, index=True),
    sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('message_logs')
