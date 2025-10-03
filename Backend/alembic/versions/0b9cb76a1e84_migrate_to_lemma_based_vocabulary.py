"""migrate to lemma based vocabulary

Revision ID: 0b9cb76a1e84
Revises: add_vocabulary_indexes
Create Date: 2025-09-28 22:02:06.663283

This migration recreates the vocabulary system with integer IDs and lemma-based approach.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0b9cb76a1e84'
down_revision: Union[str, Sequence[str], None] = 'add_vocabulary_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade to lemma-based vocabulary system with integer IDs"""

    # Check existing tables
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Drop tables that depend on vocabulary_words (if they exist)
    if 'user_vocabulary_progress' in existing_tables:
        op.drop_table('user_vocabulary_progress')

    if 'session_vocabulary' in existing_tables:
        op.drop_table('session_vocabulary')

    if 'session_word_discoveries' in existing_tables:
        op.drop_table('session_word_discoveries')

    # Drop and recreate vocabulary_words with integer ID
    if 'vocabulary_words' in existing_tables:
        op.drop_table('vocabulary_words')

    # Create new vocabulary_words table with integer IDs
    op.create_table(
        'vocabulary_words',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('word', sa.String(100), nullable=False),
        sa.Column('lemma', sa.String(100), nullable=False),
        sa.Column('language', sa.String(5), nullable=False),
        sa.Column('difficulty_level', sa.String(10), nullable=False),
        sa.Column('part_of_speech', sa.String(50), nullable=True),
        sa.Column('gender', sa.String(10), nullable=True),
        sa.Column('translation_en', sa.Text(), nullable=True),
        sa.Column('translation_native', sa.Text(), nullable=True),
        sa.Column('pronunciation', sa.String(200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('frequency_rank', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('word', 'language', name='uq_vocabulary_word_lang')
    )

    # Create indexes (if they don't exist)
    try:
        op.create_index('idx_vocabulary_lemma', 'vocabulary_words', ['lemma'])
    except:
        pass
    try:
        op.create_index('idx_vocabulary_language', 'vocabulary_words', ['language'])
    except:
        pass
    try:
        op.create_index('idx_vocabulary_level', 'vocabulary_words', ['difficulty_level'])
    except:
        pass
    try:
        op.create_index('idx_vocabulary_lemma_lang', 'vocabulary_words', ['lemma', 'language'])
    except:
        pass
    try:
        op.create_index('idx_vocabulary_word_lang', 'vocabulary_words', ['word', 'language'])
    except:
        pass

    # Create user_vocabulary_progress
    op.create_table(
        'user_vocabulary_progress',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vocabulary_id', sa.Integer(), nullable=False),
        sa.Column('lemma', sa.String(100), nullable=False),
        sa.Column('language', sa.String(5), nullable=False),
        sa.Column('is_known', sa.Boolean(), default=False, nullable=False),
        sa.Column('confidence_level', sa.Integer(), default=0, nullable=False),
        sa.Column('review_count', sa.Integer(), default=0, nullable=False),
        sa.Column('first_seen_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vocabulary_id'], ['vocabulary_words.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'vocabulary_id', name='uq_user_vocabulary')
    )

    op.create_index('idx_user_vocab_user', 'user_vocabulary_progress', ['user_id'])
    op.create_index('idx_user_vocab_lemma', 'user_vocabulary_progress', ['lemma'])
    op.create_index('idx_user_vocab_known', 'user_vocabulary_progress', ['is_known'])
    op.create_index('idx_user_vocab_user_lemma', 'user_vocabulary_progress', ['user_id', 'lemma', 'language'])

    op.create_table(
        'session_vocabulary',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('vocabulary_id', sa.Integer(), nullable=True),
        sa.Column('word', sa.String(100), nullable=False),
        sa.Column('lemma', sa.String(100), nullable=False),
        sa.Column('frequency_in_session', sa.Integer(), default=1, nullable=False),
        sa.Column('context_examples', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['processing_sessions.session_id']),
        sa.ForeignKeyConstraint(['vocabulary_id'], ['vocabulary_words.id'])
    )

    op.create_index('idx_session_vocab_session', 'session_vocabulary', ['session_id'])
    op.create_index('idx_session_vocab_word', 'session_vocabulary', ['word'])

    if 'user_language_preferences' not in existing_tables:
        op.create_table(
            'user_language_preferences',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('native_language', sa.String(5), default='en', nullable=False),
            sa.Column('target_language', sa.String(5), default='de', nullable=False),
            sa.Column('interface_language', sa.String(5), default='en', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('user_id', name='uq_user_language_pref')
        )

    if 'processing_sessions' in existing_tables:
        columns = [col['name'] for col in inspector.get_columns('processing_sessions')]
        if 'language' not in columns:
            op.add_column('processing_sessions', sa.Column('language', sa.String(5), nullable=True))

    # Import some basic German vocabulary data
    op.execute("""
        INSERT INTO vocabulary_words (word, lemma, language, difficulty_level, part_of_speech, gender, translation_en)
        VALUES
        ('Haus', 'Haus', 'de', 'A1', 'noun', 'das', 'house'),
        ('gehen', 'gehen', 'de', 'A1', 'verb', NULL, 'to go'),
        ('gut', 'gut', 'de', 'A1', 'adjective', NULL, 'good'),
        ('Fett', 'Fett', 'de', 'A2', 'noun', 'das', 'fat'),
        ('fett', 'fett', 'de', 'A2', 'adjective', NULL, 'fat (adj)'),
        ('lernen', 'lernen', 'de', 'A1', 'verb', NULL, 'to learn')
        ON CONFLICT (word, language) DO NOTHING
    """)

    print("Migration completed successfully")


def downgrade() -> None:
    """Downgrade is not supported for this migration"""
    raise NotImplementedError("Downgrade not supported - restore from database backup if needed")
