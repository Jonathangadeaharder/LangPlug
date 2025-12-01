"""
Simplified SQLAlchemy models for LangPlug - Lemma-based vocabulary system
Version 2.0 - Clean Architecture
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from core.database import Base


class User(Base):
    """User model with integer IDs"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(320), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(1024), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    # Language preferences - simplified from separate table
    native_language = Column(String(5), default="en", nullable=False)  # User's native language (e.g., "en", "es")
    target_language = Column(String(5), default="de", nullable=False)  # Language user is learning (e.g., "de", "es")

    # Learning preferences
    chunk_duration_minutes = Column(
        Integer, default=20, nullable=False
    )  # Duration of video chunks: 5, 10, or 20 minutes

    # Relationships
    refresh_token_families = relationship("RefreshTokenFamily", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuthAuditLog", back_populates="user", cascade="all, delete-orphan")
    vocabulary_progress = relationship("UserVocabularyProgress", back_populates="user", cascade="all, delete-orphan")
    game_sessions = relationship("GameSession", back_populates="user", cascade="all, delete-orphan")
    language_preferences = relationship("UserLanguagePreference", back_populates="user", cascade="all, delete-orphan")


class RefreshTokenFamily(Base):
    """Refresh token family tracking for automatic rotation and theft detection

    Token rotation works by creating a "family" of tokens where each refresh generates
    a new token in the same family. If an old token is used, it indicates token theft
    and the entire family is revoked.
    """

    __tablename__ = "refresh_token_families"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    family_id = Column(String(64), nullable=False, unique=True, index=True)  # UUID for token family
    token_hash = Column(String(128), nullable=False, unique=True, index=True)  # SHA256 of refresh token
    generation = Column(Integer, nullable=False, default=0)  # Token generation number (increments on rotation)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_used_at = Column(DateTime, nullable=True)  # Last time this token was used
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)  # True if family compromised
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(255), nullable=True)  # Why was this revoked (e.g., "token_reuse_detected")

    # Relationships
    user = relationship("User", back_populates="refresh_token_families")

    __table_args__ = (
        Index("idx_token_family_user_id", "user_id"),
        Index("idx_token_family_expires", "expires_at"),
        Index("idx_token_family_revoked", "is_revoked"),
    )


class AuthAuditLog(Base):
    """Authentication audit log for security monitoring and compliance

    Tracks all authentication-related events including:
    - Login attempts (success/failure)
    - Token refresh operations
    - Token theft detection
    - Logout events
    - Password changes
    - Account lockouts
    """

    __tablename__ = "auth_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String(50), nullable=True)  # Denormalized for deleted users
    event_type = Column(String(50), nullable=False, index=True)  # login_success, login_failure, token_refresh, etc.
    event_detail = Column(Text, nullable=True)  # Additional event information (JSON or text)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)  # Browser/client information
    success = Column(Boolean, nullable=False, index=True)  # Was the operation successful?
    failure_reason = Column(String(255), nullable=True)  # Why did it fail?
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_event_type", "event_type"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_success", "success"),
        Index("idx_audit_user_timestamp", "user_id", "timestamp"),  # Composite for user history
    )


class VocabularyWord(Base):
    """Simplified vocabulary table - lemma-based"""

    __tablename__ = "vocabulary_words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False)
    lemma = Column(String(100), nullable=False)
    language = Column(String(5), nullable=False)  # de, es, fr, etc.
    difficulty_level = Column(String(10), nullable=False)  # A1-C2
    part_of_speech = Column(String(50))  # noun, verb, adjective, etc.
    gender = Column(String(10))  # der/die/das for German
    translation_en = Column(Text)  # English translation
    translation_native = Column(Text)  # Native language translation (dynamic)
    pronunciation = Column(String(200))  # IPA or phonetic
    notes = Column(Text)  # Grammar notes, usage notes
    frequency_rank = Column(Integer)  # Word frequency ranking
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user_progress = relationship("UserVocabularyProgress", back_populates="vocabulary")
    session_vocabulary = relationship("SessionVocabulary", back_populates="vocabulary")

    __table_args__ = (
        UniqueConstraint("word", "language", name="uq_vocabulary_word_lang"),
        Index("idx_vocabulary_lemma", "lemma"),
        Index("idx_vocabulary_language", "language"),
        Index("idx_vocabulary_level", "difficulty_level"),
        Index("idx_vocabulary_lemma_lang", "lemma", "language"),
        Index("idx_vocabulary_word_lang", "word", "language"),
    )


class UserVocabularyProgress(Base):
    """User's progress tracking for vocabulary"""

    __tablename__ = "user_vocabulary_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vocabulary_id = Column(
        Integer, ForeignKey("vocabulary_words.id", ondelete="CASCADE"), nullable=True
    )  # Nullable for unknown words
    lemma = Column(String(100), nullable=False)  # Denormalized for performance
    language = Column(String(5), nullable=False)  # Denormalized for performance
    is_known = Column(Boolean, default=False, nullable=False)
    confidence_level = Column(Integer, default=0, nullable=False)  # 0-5
    review_count = Column(Integer, default=0, nullable=False)
    first_seen_at = Column(DateTime, default=func.now())
    last_reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="vocabulary_progress")
    vocabulary = relationship("VocabularyWord", back_populates="user_progress")

    __table_args__ = (
        # Note: Removed vocabulary_id from unique constraint because it can be NULL
        # Using user_id + lemma + language as unique key instead (supports unknown words)
        UniqueConstraint("user_id", "lemma", "language", name="uq_user_lemma_language"),
        Index("idx_user_vocab_user", "user_id"),
        Index("idx_user_vocab_vocab_id", "vocabulary_id"),  # For foreign key lookups
        Index("idx_user_vocab_lemma", "lemma"),
        Index("idx_user_vocab_known", "is_known"),
        Index("idx_user_vocab_user_lemma", "user_id", "lemma", "language"),
    )


class ProcessingSession(Base):
    """Video/subtitle processing sessions"""

    __tablename__ = "processing_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content_type = Column(String(50))  # video, subtitle, text
    content_path = Column(String(500))
    language = Column(String(5))  # Target language
    total_words = Column(Integer)
    unique_words = Column(Integer)
    unknown_words_count = Column(Integer)
    processing_time_seconds = Column(Float)
    status = Column(String(20), default="pending")  # pending, processing, completed, error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    vocabulary = relationship("SessionVocabulary", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_status", "status"),
        Index("idx_sessions_created", "created_at"),
    )


class SessionVocabulary(Base):
    """Vocabulary found in processing sessions"""

    __tablename__ = "session_vocabulary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), ForeignKey("processing_sessions.session_id"), nullable=False)
    vocabulary_id = Column(Integer, ForeignKey("vocabulary_words.id"), nullable=True)
    word = Column(String(100), nullable=False)
    lemma = Column(String(100), nullable=False)
    frequency_in_session = Column(Integer, default=1)
    context_examples = Column(Text)

    # Relationships
    session = relationship("ProcessingSession", back_populates="vocabulary")
    vocabulary = relationship("VocabularyWord", back_populates="session_vocabulary")

    __table_args__ = (
        Index("idx_session_vocab_session", "session_id"),
        Index("idx_session_vocab_word", "word"),
    )


class GameSession(Base):
    """Interactive vocabulary game sessions"""

    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_type = Column(String(32), nullable=False)  # vocabulary, listening, reading
    difficulty = Column(String(10), nullable=False)  # A1-C2
    language = Column(String(5), nullable=False)
    status = Column(String(20), default="active")  # active, paused, completed
    score = Column(Integer, default=0)
    max_score = Column(Integer, default=0)
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    current_question = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    session_data = Column(Text)  # JSON data for game state
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="game_sessions")

    __table_args__ = (
        Index("idx_game_sessions_user", "user_id"),
        Index("idx_game_sessions_status", "status"),
        Index("idx_game_sessions_started", "started_at"),
    )


class UserLanguagePreference(Base):
    """User language preferences"""

    __tablename__ = "user_language_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    native_language = Column(String(5), default="en", nullable=False)
    target_language = Column(String(5), default="de", nullable=False)
    interface_language = Column(String(5), default="en", nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="language_preferences")


class Language(Base):
    """Supported languages"""

    __tablename__ = "languages"

    code = Column(String(5), primary_key=True)  # ISO 639-1: de, es, en, fr
    name = Column(String(50), nullable=False)  # German, Spanish, English, French
    native_name = Column(String(50))  # Deutsch, Español, English, Français
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (Index("idx_languages_active", "is_active"),)


class UnknownWord(Base):
    """Words not in vocabulary database - for tracking and future addition"""

    __tablename__ = "unknown_words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False)
    lemma = Column(String(100))
    language = Column(String(5), nullable=False)
    frequency_count = Column(Integer, default=1)
    first_encountered = Column(DateTime, default=func.now())
    last_encountered = Column(DateTime, default=func.now(), onupdate=func.now())
    added_to_vocabulary = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("word", "language", name="uq_unknown_word_lang"),
        Index("idx_unknown_words_frequency", frequency_count.desc()),
        Index("idx_unknown_words_language", "language"),
        Index("idx_unknown_words_added", "added_to_vocabulary"),
        {"extend_existing": True},
    )
