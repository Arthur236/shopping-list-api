"""empty message

Revision ID: 10898d9c964f
Revises: 26ec23192b14
Create Date: 2017-09-24 20:53:14.219767

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '10898d9c964f'
down_revision = '26ec23192b14'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('date_created', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('date_modified', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'date_modified')
    op.drop_column('users', 'date_created')
    # ### end Alembic commands ###