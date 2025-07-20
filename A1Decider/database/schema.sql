-- A1Decider Database Schema
-- SQLite database schema for vocabulary and user data management
-- Created for ARCH-04 Database Migration

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Word Categories Table
-- Stores hierarchical categories for organizing vocabulary
CREATE TABLE IF NOT EXISTS word_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    language TEXT NOT NULL DEFAULT 'de',
    parent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES word_categories(id) ON DELETE SET NULL,
    UNIQUE(name, language)
);

-- Vocabulary Table
-- Main vocabulary storage with word details
CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    lemma TEXT,
    frequency INTEGER DEFAULT 0,
    difficulty_level TEXT DEFAULT 'unknown',
    language TEXT NOT NULL DEFAULT 'de',
    part_of_speech TEXT,
    definition TEXT,
    example_sentence TEXT,
    pronunciation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(word, language)
);

-- Word Category Associations Table
-- Many-to-many relationship between words and categories
CREATE TABLE IF NOT EXISTS word_category_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (word_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES word_categories(id) ON DELETE CASCADE,
    UNIQUE(word_id, category_id)
);

-- Unknown Words Table
-- Tracks words that are not yet in the vocabulary
CREATE TABLE IF NOT EXISTS unknown_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    lemma TEXT,
    frequency_count INTEGER DEFAULT 1,
    language TEXT NOT NULL DEFAULT 'de',
    first_encountered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_encountered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(word, language)
);

-- User Learning Progress Table
-- Tracks individual word learning progress
CREATE TABLE IF NOT EXISTS user_learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    proficiency_level TEXT DEFAULT 'beginner',
    confidence_score REAL DEFAULT 0.0,
    language TEXT NOT NULL DEFAULT 'de',
    first_learned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reviewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    review_count INTEGER DEFAULT 0,
    
    UNIQUE(word, language),
    CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0)
);

-- Processing Sessions Table
-- Tracks subtitle processing and learning sessions
CREATE TABLE IF NOT EXISTS processing_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_type TEXT NOT NULL DEFAULT 'subtitle_processing',
    source_file TEXT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    words_processed INTEGER DEFAULT 0,
    new_words_discovered INTEGER DEFAULT 0,
    metadata TEXT -- JSON string for additional session data
);

-- Session Word Discoveries Table
-- Tracks words discovered during specific sessions
CREATE TABLE IF NOT EXISTS session_word_discoveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    discovery_context TEXT,
    frequency_in_session INTEGER DEFAULT 1,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES processing_sessions(id) ON DELETE CASCADE
);

-- Indexes for Performance Optimization

-- Word Categories Indexes
CREATE INDEX IF NOT EXISTS idx_word_categories_language ON word_categories(language);
CREATE INDEX IF NOT EXISTS idx_word_categories_parent ON word_categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_word_categories_name_lang ON word_categories(name, language);

-- Vocabulary Indexes
CREATE INDEX IF NOT EXISTS idx_vocabulary_word_lang ON vocabulary(word, language);
CREATE INDEX IF NOT EXISTS idx_vocabulary_language ON vocabulary(language);
CREATE INDEX IF NOT EXISTS idx_vocabulary_difficulty ON vocabulary(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_vocabulary_frequency ON vocabulary(frequency DESC);
CREATE INDEX IF NOT EXISTS idx_vocabulary_lemma ON vocabulary(lemma);
CREATE INDEX IF NOT EXISTS idx_vocabulary_created ON vocabulary(created_at);

-- Word Category Associations Indexes
CREATE INDEX IF NOT EXISTS idx_wca_word_id ON word_category_associations(word_id);
CREATE INDEX IF NOT EXISTS idx_wca_category_id ON word_category_associations(category_id);

-- Unknown Words Indexes
CREATE INDEX IF NOT EXISTS idx_unknown_words_word_lang ON unknown_words(word, language);
CREATE INDEX IF NOT EXISTS idx_unknown_words_language ON unknown_words(language);
CREATE INDEX IF NOT EXISTS idx_unknown_words_frequency ON unknown_words(frequency_count DESC);
CREATE INDEX IF NOT EXISTS idx_unknown_words_last_encountered ON unknown_words(last_encountered DESC);
CREATE INDEX IF NOT EXISTS idx_unknown_words_first_encountered ON unknown_words(first_encountered DESC);

-- User Learning Progress Indexes
CREATE INDEX IF NOT EXISTS idx_ulp_word_lang ON user_learning_progress(word, language);
CREATE INDEX IF NOT EXISTS idx_ulp_language ON user_learning_progress(language);
CREATE INDEX IF NOT EXISTS idx_ulp_proficiency ON user_learning_progress(proficiency_level);
CREATE INDEX IF NOT EXISTS idx_ulp_confidence ON user_learning_progress(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_ulp_last_reviewed ON user_learning_progress(last_reviewed);
CREATE INDEX IF NOT EXISTS idx_ulp_review_count ON user_learning_progress(review_count DESC);

-- Processing Sessions Indexes
CREATE INDEX IF NOT EXISTS idx_sessions_type ON processing_sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON processing_sessions(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_end_time ON processing_sessions(end_time DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_source_file ON processing_sessions(source_file);

-- Session Word Discoveries Indexes
CREATE INDEX IF NOT EXISTS idx_swd_session_id ON session_word_discoveries(session_id);
CREATE INDEX IF NOT EXISTS idx_swd_word ON session_word_discoveries(word);
CREATE INDEX IF NOT EXISTS idx_swd_discovered_at ON session_word_discoveries(discovered_at DESC);

-- Full-text search indexes (if needed for advanced search)
-- Note: These are optional and can be added later if full-text search is required
-- CREATE VIRTUAL TABLE IF NOT EXISTS vocabulary_fts USING fts5(word, definition, example_sentence, content='vocabulary', content_rowid='id');
-- CREATE VIRTUAL TABLE IF NOT EXISTS unknown_words_fts USING fts5(word, content='unknown_words', content_rowid='id');

-- Views for Common Queries

-- View: Word Statistics
CREATE VIEW IF NOT EXISTS word_statistics AS
SELECT 
    language,
    COUNT(*) as total_vocabulary_words,
    AVG(frequency) as avg_frequency,
    COUNT(CASE WHEN difficulty_level = 'beginner' THEN 1 END) as beginner_words,
    COUNT(CASE WHEN difficulty_level = 'intermediate' THEN 1 END) as intermediate_words,
    COUNT(CASE WHEN difficulty_level = 'advanced' THEN 1 END) as advanced_words,
    COUNT(CASE WHEN difficulty_level = 'unknown' THEN 1 END) as unknown_difficulty_words
FROM vocabulary
GROUP BY language;

-- View: Unknown Words Statistics
CREATE VIEW IF NOT EXISTS unknown_words_statistics AS
SELECT 
    language,
    COUNT(*) as total_unknown_words,
    SUM(frequency_count) as total_frequency,
    AVG(frequency_count) as avg_frequency,
    MAX(frequency_count) as max_frequency,
    COUNT(CASE WHEN frequency_count = 1 THEN 1 END) as single_occurrence_words,
    COUNT(CASE WHEN frequency_count > 10 THEN 1 END) as frequent_unknown_words
FROM unknown_words
GROUP BY language;

-- View: Learning Progress Summary
CREATE VIEW IF NOT EXISTS learning_progress_summary AS
SELECT 
    language,
    COUNT(*) as total_words_learning,
    AVG(confidence_score) as avg_confidence,
    COUNT(CASE WHEN proficiency_level = 'beginner' THEN 1 END) as beginner_level,
    COUNT(CASE WHEN proficiency_level = 'intermediate' THEN 1 END) as intermediate_level,
    COUNT(CASE WHEN proficiency_level = 'advanced' THEN 1 END) as advanced_level,
    COUNT(CASE WHEN last_reviewed < datetime('now', '-7 days') THEN 1 END) as needs_review
FROM user_learning_progress
GROUP BY language;

-- View: Recent Activity
CREATE VIEW IF NOT EXISTS recent_activity AS
SELECT 
    'session' as activity_type,
    ps.id as activity_id,
    ps.session_type as activity_description,
    ps.start_time as activity_time,
    ps.words_processed as activity_count
FROM processing_sessions ps
WHERE ps.start_time >= datetime('now', '-30 days')
UNION ALL
SELECT 
    'word_discovery' as activity_type,
    swd.id as activity_id,
    'Word discovered: ' || swd.word as activity_description,
    swd.discovered_at as activity_time,
    swd.frequency_in_session as activity_count
FROM session_word_discoveries swd
WHERE swd.discovered_at >= datetime('now', '-30 days')
ORDER BY activity_time DESC;

-- Triggers for Automatic Updates

-- Update vocabulary updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_vocabulary_timestamp 
AFTER UPDATE ON vocabulary
FOR EACH ROW
BEGIN
    UPDATE vocabulary SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update unknown words last_encountered timestamp
CREATE TRIGGER IF NOT EXISTS update_unknown_words_timestamp 
AFTER UPDATE ON unknown_words
FOR EACH ROW
WHEN NEW.frequency_count > OLD.frequency_count
BEGIN
    UPDATE unknown_words SET last_encountered = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update learning progress last_reviewed timestamp
CREATE TRIGGER IF NOT EXISTS update_learning_progress_timestamp 
AFTER UPDATE ON user_learning_progress
FOR EACH ROW
WHEN NEW.review_count > OLD.review_count
BEGIN
    UPDATE user_learning_progress SET last_reviewed = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Insert default word categories
INSERT OR IGNORE INTO word_categories (name, description, language) VALUES
('Nouns', 'Substantive - naming words for people, places, things', 'de'),
('Verbs', 'Verben - action and state words', 'de'),
('Adjectives', 'Adjektive - descriptive words', 'de'),
('Adverbs', 'Adverbien - words that modify verbs, adjectives, or other adverbs', 'de'),
('Prepositions', 'Präpositionen - words that show relationships between other words', 'de'),
('Conjunctions', 'Konjunktionen - connecting words', 'de'),
('Articles', 'Artikel - definite and indefinite articles', 'de'),
('Pronouns', 'Pronomen - words that replace nouns', 'de'),
('Numbers', 'Zahlen - cardinal and ordinal numbers', 'de'),
('Common Words', 'Häufige Wörter - most frequently used words', 'de'),
('Academic', 'Akademische Wörter - academic and formal vocabulary', 'de'),
('Everyday', 'Alltägliche Wörter - everyday conversation vocabulary', 'de'),
('Technical', 'Technische Begriffe - technical and specialized terms', 'de'),
('Idioms', 'Redewendungen - idiomatic expressions', 'de'),
('Slang', 'Umgangssprache - informal and colloquial expressions', 'de');

-- Database version and metadata
CREATE TABLE IF NOT EXISTS database_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO database_metadata (key, value) VALUES
('schema_version', '1.0.0'),
('created_at', datetime('now')),
('description', 'A1Decider vocabulary and user data database'),
('migration_source', 'ARCH-04 Database Migration from flat files');

-- Performance optimization settings
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456; -- 256MB