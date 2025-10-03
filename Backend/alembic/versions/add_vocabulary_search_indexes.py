"""Add vocabulary search indexes for lemma-based schema"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_vocabulary_indexes'
down_revision = '10f18f66a1df'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add optimized indexes for the simplified vocabulary tables."""
    # Fixed: use 'language' instead of 'language_code', 'user_vocabulary_progress' instead of 'user_known_words'
    op.execute(sa.text('CREATE INDEX IF NOT EXISTS idx_vocabulary_words_lower_lemma ON vocabulary_words (LOWER(lemma))'))
    op.execute(sa.text('CREATE INDEX IF NOT EXISTS idx_vocabulary_words_language_lemma_word ON vocabulary_words (language, lemma, word)'))
    op.execute(sa.text('CREATE INDEX IF NOT EXISTS idx_user_vocabulary_progress_language_lemma ON user_vocabulary_progress (language, lemma)'))
    op.execute(sa.text('CREATE INDEX IF NOT EXISTS idx_user_vocabulary_progress_user_language ON user_vocabulary_progress (user_id, language)'))


def downgrade() -> None:
    """Remove lemma-based vocabulary indexes."""
    op.execute(sa.text('DROP INDEX IF EXISTS idx_user_vocabulary_progress_user_language'))
    op.execute(sa.text('DROP INDEX IF EXISTS idx_user_vocabulary_progress_language_lemma'))
    op.execute(sa.text('DROP INDEX IF EXISTS idx_vocabulary_words_language_lemma_word'))
    op.execute(sa.text('DROP INDEX IF EXISTS idx_vocabulary_words_lower_lemma'))
