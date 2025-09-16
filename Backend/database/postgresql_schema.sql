-- PostgreSQL Schema for LangPlug Application
-- Converted from SQLite schema with PostgreSQL-specific optimizations

-- Enable UUID extension for better session tokens
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(320) UNIQUE NOT NULL,
    hashed_password VARCHAR(1024) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_superuser BOOLEAN DEFAULT FALSE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    native_language VARCHAR(10) DEFAULT 'en',
    target_language VARCHAR(10) DEFAULT 'de'
);

-- User sessions table with UUID token
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(128) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Videos table
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_path VARCHAR(500) NOT NULL,
    subtitle_path VARCHAR(500),
    language VARCHAR(10) DEFAULT 'en',
    difficulty_level VARCHAR(20) DEFAULT 'intermediate',
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Word categories table
CREATE TABLE IF NOT EXISTS word_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    file_path VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vocabulary table
CREATE TABLE IF NOT EXISTS vocabulary (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) NOT NULL,
    lemma VARCHAR(100),
    language VARCHAR(10) DEFAULT 'de',
    difficulty_level VARCHAR(10),
    word_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(word, language)
);

-- Word category associations
CREATE TABLE IF NOT EXISTS word_category_associations (
    id SERIAL PRIMARY KEY,
    word_id INTEGER REFERENCES vocabulary(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES word_categories(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(word_id, category_id)
);

-- Unknown words table
CREATE TABLE IF NOT EXISTS unknown_words (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) NOT NULL,
    lemma VARCHAR(100),
    frequency_count INTEGER DEFAULT 1,
    first_encountered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_encountered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    language VARCHAR(10) DEFAULT 'de',
    UNIQUE(word, language)
);

-- User learning progress
CREATE TABLE IF NOT EXISTS user_learning_progress (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) DEFAULT 'default_user',
    word_id INTEGER REFERENCES vocabulary(id) ON DELETE CASCADE,
    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_level INTEGER DEFAULT 1,
    review_count INTEGER DEFAULT 0,
    last_reviewed TIMESTAMP,
    UNIQUE(user_id, word_id)
);

-- Processing sessions
CREATE TABLE IF NOT EXISTS processing_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    content_type VARCHAR(50),
    content_path VARCHAR(500),
    total_words INTEGER,
    unknown_words_found INTEGER,
    processing_time_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Session word discoveries
CREATE TABLE IF NOT EXISTS session_word_discoveries (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) REFERENCES processing_sessions(session_id) ON DELETE CASCADE,
    word VARCHAR(100) NOT NULL,
    frequency_in_session INTEGER DEFAULT 1,
    context_examples TEXT
);

-- Database metadata
CREATE TABLE IF NOT EXISTS database_metadata (
    key VARCHAR(255) PRIMARY KEY,
    value VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance optimization

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);

-- User sessions indexes
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active);

-- Videos table indexes
CREATE INDEX IF NOT EXISTS idx_videos_title ON videos(title);
CREATE INDEX IF NOT EXISTS idx_videos_language ON videos(language);
CREATE INDEX IF NOT EXISTS idx_videos_difficulty ON videos(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_videos_created ON videos(created_at);

-- Vocabulary table indexes
CREATE INDEX IF NOT EXISTS idx_vocabulary_word ON vocabulary(word);
CREATE INDEX IF NOT EXISTS idx_vocabulary_lemma ON vocabulary(lemma);
CREATE INDEX IF NOT EXISTS idx_vocabulary_difficulty ON vocabulary(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_vocabulary_language ON vocabulary(language);
CREATE INDEX IF NOT EXISTS idx_vocabulary_word_lang ON vocabulary(word, language);

-- Unknown words indexes
CREATE INDEX IF NOT EXISTS idx_unknown_words_word ON unknown_words(word);
CREATE INDEX IF NOT EXISTS idx_unknown_words_frequency ON unknown_words(frequency_count DESC);
CREATE INDEX IF NOT EXISTS idx_unknown_words_word_lang ON unknown_words(word, language);
CREATE INDEX IF NOT EXISTS idx_unknown_words_language ON unknown_words(language);
CREATE INDEX IF NOT EXISTS idx_unknown_words_last_encountered ON unknown_words(last_encountered DESC);

-- User learning progress indexes
CREATE INDEX IF NOT EXISTS idx_user_progress_user ON user_learning_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_ulp_word_id ON user_learning_progress(word_id);
CREATE INDEX IF NOT EXISTS idx_ulp_confidence ON user_learning_progress(confidence_level DESC);
CREATE INDEX IF NOT EXISTS idx_ulp_last_reviewed ON user_learning_progress(last_reviewed);

-- Processing sessions indexes
CREATE INDEX IF NOT EXISTS idx_sessions_type ON processing_sessions(content_type);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON processing_sessions(created_at);

-- Session word discoveries indexes
CREATE INDEX IF NOT EXISTS idx_session_discoveries_session ON session_word_discoveries(session_id);
CREATE INDEX IF NOT EXISTS idx_swd_word ON session_word_discoveries(word);

-- Trigger to automatically update updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_videos_updated_at BEFORE UPDATE ON videos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_word_categories_updated_at BEFORE UPDATE ON word_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vocabulary_updated_at BEFORE UPDATE ON vocabulary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_database_metadata_updated_at BEFORE UPDATE ON database_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial database metadata
INSERT INTO database_metadata (key, value) VALUES ('schema_version', '1.0') ON CONFLICT (key) DO NOTHING;
INSERT INTO database_metadata (key, value) VALUES ('migration_date', CURRENT_TIMESTAMP::TEXT) ON CONFLICT (key) DO NOTHING;
