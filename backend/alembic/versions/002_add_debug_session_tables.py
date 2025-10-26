"""add debug session tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create debug_sessions table
    op.create_table(
        'debug_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('target_url', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('stopped_at', sa.DateTime(), nullable=True),
        sa.Column('duration_limit', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_debug_sessions_id'), 'debug_sessions', ['id'], unique=False)
    
    # Create network_events table
    op.create_table(
        'network_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('method', sa.String(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('request_headers', sa.Text(), nullable=True),
        sa.Column('response_headers', sa.Text(), nullable=True),
        sa.Column('request_body', sa.Text(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('timing', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['debug_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_network_events_id'), 'network_events', ['id'], unique=False)
    op.create_index(op.f('ix_network_events_session_id'), 'network_events', ['session_id'], unique=False)
    
    # Create console_errors table
    op.create_table(
        'console_errors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['debug_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_console_errors_id'), 'console_errors', ['id'], unique=False)
    op.create_index(op.f('ix_console_errors_session_id'), 'console_errors', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_console_errors_session_id'), table_name='console_errors')
    op.drop_index(op.f('ix_console_errors_id'), table_name='console_errors')
    op.drop_table('console_errors')
    
    op.drop_index(op.f('ix_network_events_session_id'), table_name='network_events')
    op.drop_index(op.f('ix_network_events_id'), table_name='network_events')
    op.drop_table('network_events')
    
    op.drop_index(op.f('ix_debug_sessions_id'), table_name='debug_sessions')
    op.drop_table('debug_sessions')
