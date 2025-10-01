-- Simple vocabulary schema without concepts
-- Just track words, lemmas, and user knowledge

-- Table for vocabulary words with their lemmas and difficulty levels
CREATE TABLE IF NOT EXISTS vocabulary_words (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    language_code VARCHAR(5) NOT NULL,
    word VARCHAR(100) NOT NULL,
    lemma VARCHAR(100) NOT NULL,
    difficulty_level VARCHAR(2) NOT NULL CHECK (difficulty_level IN ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(language_code, lemma)
);

-- Table for user's known words (by lemma)
CREATE TABLE IF NOT EXISTS user_known_words (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    language_code VARCHAR(5) NOT NULL,
    lemma VARCHAR(100) NOT NULL,
    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, language_code, lemma)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_vocabulary_words_lemma ON vocabulary_words(language_code, lemma);
CREATE INDEX IF NOT EXISTS idx_vocabulary_words_level ON vocabulary_words(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_user_known_words_user ON user_known_words(user_id);
CREATE INDEX IF NOT EXISTS idx_user_known_words_lemma ON user_known_words(user_id, language_code, lemma);
