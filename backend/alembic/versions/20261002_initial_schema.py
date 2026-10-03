"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-10-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create analyses table
    op.create_table(
        'analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'UPLOADING', 'VALIDATING', 'PROCESSING', 'COMPLETED', 'FAILED', name='analysisstatus'), nullable=False),
        sa.Column('current_stage', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analyses_id'), 'analyses', ['id'], unique=False)

    # Create assets table
    op.create_table(
        'assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('creative_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('cloudinary_public_id', sa.String(), nullable=True),
        sa.Column('cloudinary_url', sa.String(), nullable=True),
        sa.Column('secure_url', sa.String(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('format', sa.String(), nullable=True),
        sa.Column('bytes', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assets_creative_id'), 'assets', ['creative_id'], unique=False)
    op.create_index(op.f('ix_assets_id'), 'assets', ['id'], unique=False)

    # Create performance_records table
    op.create_table(
        'performance_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('creative_id', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('impressions', sa.Integer(), nullable=False),
        sa.Column('clicks', sa.Integer(), nullable=False),
        sa.Column('conversions', sa.Integer(), nullable=False),
        sa.Column('spend', sa.Float(), nullable=False),
        sa.Column('revenue', sa.Float(), nullable=False),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_performance_records_creative_id'), 'performance_records', ['creative_id'], unique=False)
    op.create_index(op.f('ix_performance_records_id'), 'performance_records', ['id'], unique=False)

    # Create creative_features table
    op.create_table(
        'creative_features',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('creative_id', sa.String(), nullable=False),
        sa.Column('aspect_ratio', sa.Float(), nullable=True),
        sa.Column('brightness', sa.Float(), nullable=True),
        sa.Column('contrast', sa.Float(), nullable=True),
        sa.Column('edge_density', sa.Float(), nullable=True),
        sa.Column('dominant_color', sa.String(), nullable=True),
        sa.Column('bright_background', sa.Boolean(), nullable=True),
        sa.Column('portrait', sa.Boolean(), nullable=True),
        sa.Column('landscape', sa.Boolean(), nullable=True),
        sa.Column('human_present', sa.Boolean(), nullable=True),
        sa.Column('feature_sources', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_creative_features_creative_id'), 'creative_features', ['creative_id'], unique=False)
    op.create_index(op.f('ix_creative_features_id'), 'creative_features', ['id'], unique=False)

    # Create creative_dna_insights table
    op.create_table(
        'creative_dna_insights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('feature_name', sa.String(), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('positive_group', sa.String(), nullable=False),
        sa.Column('negative_group', sa.String(), nullable=False),
        sa.Column('positive_median', sa.Float(), nullable=False),
        sa.Column('negative_median', sa.Float(), nullable=False),
        sa.Column('percent_difference', sa.Float(), nullable=False),
        sa.Column('sample_size_positive', sa.Integer(), nullable=False),
        sa.Column('sample_size_negative', sa.Integer(), nullable=False),
        sa.Column('p_value', sa.Float(), nullable=True),
        sa.Column('effect_size', sa.Float(), nullable=True),
        sa.Column('evidence_tier', sa.String(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_creative_dna_insights_feature_name'), 'creative_dna_insights', ['feature_name'], unique=False)
    op.create_index(op.f('ix_creative_dna_insights_id'), 'creative_dna_insights', ['id'], unique=False)
    op.create_index(op.f('ix_creative_dna_insights_metric_name'), 'creative_dna_insights', ['metric_name'], unique=False)

    # Create generated_assets table
    op.create_table(
        'generated_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('source_asset_id', sa.Integer(), nullable=False),
        sa.Column('format', sa.String(), nullable=False),
        sa.Column('transformation', sa.JSON(), nullable=True),
        sa.Column('generated_url', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
        sa.ForeignKeyConstraint(['source_asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generated_assets_id'), 'generated_assets', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_generated_assets_id'), table_name='generated_assets')
    op.drop_table('generated_assets')
    op.drop_index(op.f('ix_creative_dna_insights_metric_name'), table_name='creative_dna_insights')
    op.drop_index(op.f('ix_creative_dna_insights_id'), table_name='creative_dna_insights')
    op.drop_index(op.f('ix_creative_dna_insights_feature_name'), table_name='creative_dna_insights')
    op.drop_table('creative_dna_insights')
    op.drop_index(op.f('ix_creative_features_id'), table_name='creative_features')
    op.drop_index(op.f('ix_creative_features_creative_id'), table_name='creative_features')
    op.drop_table('creative_features')
    op.drop_index(op.f('ix_performance_records_id'), table_name='performance_records')
    op.drop_index(op.f('ix_performance_records_creative_id'), table_name='performance_records')
    op.drop_table('performance_records')
    op.drop_index(op.f('ix_assets_id'), table_name='assets')
    op.drop_index(op.f('ix_assets_creative_id'), table_name='assets')
    op.drop_table('assets')
    op.drop_index(op.f('ix_analyses_id'), table_name='analyses')
    op.drop_table('analyses')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
