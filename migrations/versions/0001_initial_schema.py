"""initial schema: users, screenings, candidates

Revision ID: 0001_initial
Revises: 
Create Date: 2026-10-07 13:31:40.769761

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('session_token', sa.String(length=64), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('failed_logins', sa.Integer(), nullable=False),
    sa.Column('locked_until', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('last_login_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    op.create_table('screenings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('job_title', sa.String(length=200), nullable=False),
    sa.Column('job_description', sa.Text(), nullable=False),
    sa.Column('job_info', sa.JSON(), nullable=False),
    sa.Column('top_n', sa.Integer(), nullable=False),
    sa.Column('total', sa.Integer(), nullable=False),
    sa.Column('errors', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('screenings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_screenings_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_screenings_user_id'), ['user_id'], unique=False)

    op.create_table('candidates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('screening_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('rank', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=True),
    sa.Column('phone', sa.String(length=60), nullable=True),
    sa.Column('score', sa.Float(), nullable=False),
    sa.Column('grade', sa.String(length=30), nullable=False),
    sa.Column('recommended', sa.Boolean(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('notes', sa.Text(), nullable=False),
    sa.Column('experience_years', sa.Float(), nullable=False),
    sa.Column('education_label', sa.String(length=60), nullable=True),
    sa.Column('predicted_role', sa.String(length=80), nullable=True),
    sa.Column('search_text', sa.Text(), nullable=False),
    sa.Column('data', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('shortlisted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['screening_id'], ['screenings.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('candidates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_candidates_score'), ['score'], unique=False)
        batch_op.create_index(batch_op.f('ix_candidates_screening_id'), ['screening_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_candidates_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_candidates_user_id'), ['user_id'], unique=False)




def downgrade():

    with op.batch_alter_table('candidates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_candidates_user_id'))
        batch_op.drop_index(batch_op.f('ix_candidates_status'))
        batch_op.drop_index(batch_op.f('ix_candidates_screening_id'))
        batch_op.drop_index(batch_op.f('ix_candidates_score'))

    op.drop_table('candidates')
    with op.batch_alter_table('screenings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_screenings_user_id'))
        batch_op.drop_index(batch_op.f('ix_screenings_created_at'))

    op.drop_table('screenings')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')

