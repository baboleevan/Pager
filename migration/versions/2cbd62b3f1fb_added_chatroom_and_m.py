"""added ChatRoom and Message

Revision ID: 2cbd62b3f1fb
Revises: 11d26e86341a
Create Date: 2013-02-07 20:45:27.419947

"""

# revision identifiers, used by Alembic.
revision = '2cbd62b3f1fb'
down_revision = '11d26e86341a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('chat_rooms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('creator_id', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(True), nullable=False),
    sa.Column('updated', sa.DateTime(True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(True), nullable=False),
    sa.Column('updated', sa.DateTime(True), nullable=False),
    sa.Column('color', sa.Integer(), nullable=False),
    sa.Column('message', sa.String(length=280), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
    sa.Column('chat_room_id', sa.Integer(), nullable=False, index=True),
    sa.ForeignKeyConstraint(['chat_room_id'], ['chat_rooms.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users_in_chat_room',
    sa.Column('chat_room_id', sa.Integer(), nullable=False, index=True),
    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
    sa.Column('created', sa.DateTime(True), nullable=False, index=True),
    sa.ForeignKeyConstraint(['chat_room_id'], ['chat_rooms.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('chat_room_id', 'user_id')
    )


def downgrade():
    op.drop_table('users_in_chat_room')
    op.drop_table('messages')
    op.drop_table('chat_rooms')
