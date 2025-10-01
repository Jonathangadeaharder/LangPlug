"""Initial migration - Database-agnostic schema creation"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision: str = '879b4bfbd98e'
down_revision: str | None = None
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    """Create all database tables."""

    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('email', sa.String(320), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('hashed_password', sa.String(1024), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=func.now(), onupdate=func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # Languages table
    op.create_table(
        'languages',
        sa.Column('code', sa.String(5), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('native_name', sa.String(50)),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=func.now()),
        sa.PrimaryKeyConstraint('code')
    )
    op.create_index('idx_languages_active', 'languages', ['is_active'])

    # Vocabulary words table
    op.create_table(
        'vocabulary_words',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('word', sa.String(100), nullable=False),
        sa.Column('lemma', sa.String(100), nullable=False),
        sa.Column('language', sa.String(5), nullable=False),
        sa.Column('difficulty_level', sa.String(10), nullable=False),
        sa.Column('part_of_speech', sa.String(50)),
        sa.Column('gender', sa.String(10)),
        sa.Column('translation_en', sa.Text()),
        sa.Column('translation_native', sa.Text()),
        sa.Column('pronunciation', sa.String(200)),
        sa.Column('notes', sa.Text()),
        sa.Column('frequency_rank', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=func.now(), onupdate=func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('word', 'language', name='uq_vocabulary_word_lang')
    )
    op.create_index('idx_vocabulary_lemma', 'vocabulary_words', ['lemma'])
    op.create_index('idx_vocabulary_language', 'vocabulary_words', ['language'])
    op.create_index('idx_vocabulary_level', 'vocabulary_words', ['difficulty_level'])
    op.create_index('idx_vocabulary_lemma_lang', 'vocabulary_words', ['lemma', 'language'])
    op.create_index('idx_vocabulary_word_lang', 'vocabulary_words', ['word', 'language'])

    # User vocabulary progress table
    op.create_table(
        'user_vocabulary_progress',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vocabulary_id', sa.Integer(), nullable=False),
        sa.Column('lemma', sa.String(100), nullable=False),
        sa.Column('language', sa.String(5), nullable=False),
        sa.Column('is_known', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('confidence_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('first_seen_at', sa.DateTime(), server_default=func.now()),
        sa.Column('last_reviewed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=func.now(), onupdate=func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vocabulary_id'], ['vocabulary_words.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'vocabulary_id', name='uq_user_vocabulary')
    )
    op.create_index('idx_user_vocab_user', 'user_vocabulary_progress', ['user_id'])
    op.create_index('idx_user_vocab_lemma', 'user_vocabulary_progress', ['lemma'])
    op.create_index('idx_user_vocab_known', 'user_vocabulary_progress', ['is_known'])
    op.create_index('idx_user_vocab_user_lemma', 'user_vocabulary_progress', ['user_id', 'lemma', 'language'])

    # Processing sessions table
    op.create_table(
        'processing_sessions',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.Integer()),
        sa.Column('content_type', sa.String(50)),
        sa.Column('content_path', sa.String(500)),
        sa.Column('language', sa.String(5)),
        sa.Column('total_words', sa.Integer()),
        sa.Column('unique_words', sa.Integer()),
        sa.Column('unknown_words_count', sa.Integer()),
        sa.Column('processing_time_seconds', sa.Float()),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=func.now()),
        sa.Column('completed_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('idx_sessions_user', 'processing_sessions', ['user_id'])
    op.create_index('idx_sessions_status', 'processing_sessions', ['status'])
    op.create_index('idx_sessions_created', 'processing_sessions', ['created_at'])

    # Session vocabulary table
    op.create_table(
        'session_vocabulary',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('vocabulary_id', sa.Integer()),
        sa.Column('word', sa.String(100), nullable=False),
        sa.Column('lemma', sa.String(100), nullable=False),
        sa.Column('frequency_in_session', sa.Integer(), server_default='1'),
        sa.Column('context_examples', sa.Text()),
        sa.ForeignKeyConstraint(['session_id'], ['processing_sessions.session_id']),
        sa.ForeignKeyConstraint(['vocabulary_id'], ['vocabulary_words.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_session_vocab_session', 'session_vocabulary', ['session_id'])
    op.create_index('idx_session_vocab_word', 'session_vocabulary', ['word'])

    # Game sessions table
    op.create_table(
        'game_sessions',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('game_type', sa.String(32), nullable=False),
        sa.Column('difficulty', sa.String(10), nullable=False),
        sa.Column('language', sa.String(5), nullable=False),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('score', sa.Integer(), server_default='0'),
        sa.Column('max_score', sa.Integer(), server_default='0'),
        sa.Column('questions_answered', sa.Integer(), server_default='0'),
        sa.Column('correct_answers', sa.Integer(), server_default='0'),
        sa.Column('total_questions', sa.Integer(), server_default='0'),
        sa.Column('session_data', sa.Text()),
        sa.Column('started_at', sa.DateTime(), server_default=func.now()),
        sa.Column('completed_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('idx_game_sessions_user', 'game_sessions', ['user_id'])
    op.create_index('idx_game_sessions_status', 'game_sessions', ['status'])
    op.create_index('idx_game_sessions_started', 'game_sessions', ['started_at'])

    # User language preferences table
    op.create_table(
        'user_language_preferences',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('native_language', sa.String(5), nullable=False, server_default='en'),
        sa.Column('target_language', sa.String(5), nullable=False, server_default='de'),
        sa.Column('interface_language', sa.String(5), nullable=False, server_default='en'),
        sa.Column('created_at', sa.DateTime(), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=func.now(), onupdate=func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Unknown words table
    op.create_table(
        'unknown_words',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('word', sa.String(100), nullable=False),
        sa.Column('lemma', sa.String(100)),
        sa.Column('language', sa.String(5), nullable=False),
        sa.Column('frequency_count', sa.Integer(), server_default='1'),
        sa.Column('first_encountered', sa.DateTime(), server_default=func.now()),
        sa.Column('last_encountered', sa.DateTime(), server_default=func.now(), onupdate=func.now()),
        sa.Column('added_to_vocabulary', sa.Boolean(), server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('word', 'language', name='uq_unknown_word_lang')
    )
    op.create_index('idx_unknown_words_frequency', 'unknown_words', [sa.text('frequency_count DESC')])
    op.create_index('idx_unknown_words_language', 'unknown_words', ['language'])
    op.create_index('idx_unknown_words_added', 'unknown_words', ['added_to_vocabulary'])

    # Legacy vocabulary concepts table for test compatibility
    op.create_table(
        'vocabulary_concepts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('difficulty_level', sa.String(5), nullable=False),
        sa.Column('semantic_category', sa.String(50)),
        sa.Column('domain', sa.String(50)),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('vocabulary_concepts')
    op.drop_table('unknown_words')
    op.drop_table('user_language_preferences')
    op.drop_table('game_sessions')
    op.drop_table('session_vocabulary')
    op.drop_table('processing_sessions')
    op.drop_table('user_vocabulary_progress')
    op.drop_table('vocabulary_words')
    op.drop_table('languages')
    op.drop_table('users')
