"""
SQLAlchemy models for the LangPlug database
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

from core.auth import Base, User


class WordCategory(Base):
    """Word Categories Table"""
    __tablename__ = 'word_categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    file_path = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    word_associations = relationship("WordCategoryAssociation", back_populates="category")


class Vocabulary(Base):
    """Vocabulary Table"""
    __tablename__ = 'vocabulary'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False)
    lemma = Column(String(100))
    language = Column(String(10), default='de')
    difficulty_level = Column(String(10))
    word_type = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    category_associations = relationship("WordCategoryAssociation", back_populates="word")
    learning_progress = relationship("UserLearningProgress", back_populates="vocabulary_word")
    word_discoveries = relationship("SessionWordDiscovery", back_populates="vocabulary_word")

    __table_args__ = (
        UniqueConstraint('word', 'language'),
        Index('idx_vocabulary_word', 'word'),
        Index('idx_vocabulary_lemma', 'lemma'),
        Index('idx_vocabulary_difficulty', 'difficulty_level'),
        Index('idx_vocabulary_created', 'created_at'),
    )


class WordCategoryAssociation(Base):
    """Word Category Associations Table"""
    __tablename__ = 'word_category_associations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word_id = Column(Integer, ForeignKey('vocabulary.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('word_categories.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    word = relationship("Vocabulary", back_populates="category_associations")
    category = relationship("WordCategory", back_populates="word_associations")

    __table_args__ = (
        UniqueConstraint('word_id', 'category_id'),
    )


class UnknownWord(Base):
    """Unknown Words Table"""
    __tablename__ = 'unknown_words'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False)
    lemma = Column(String(100))
    frequency_count = Column(Integer, default=1)
    first_encountered = Column(DateTime, default=func.now())
    last_encountered = Column(DateTime, default=func.now(), onupdate=func.now())
    language = Column(String(10), default='de')

    __table_args__ = (
        UniqueConstraint('word', 'language'),
        Index('idx_unknown_words_word', 'word'),
        Index('idx_unknown_words_frequency', frequency_count.desc()),
        Index('idx_unknown_words_word_lang', 'word', 'language'),
        Index('idx_unknown_words_language', 'language'),
        Index('idx_unknown_words_last_encountered', last_encountered.desc()),
        Index('idx_unknown_words_first_encountered', first_encountered.desc()),
    )


class UserLearningProgress(Base):
    """User Learning Progress Table"""
    __tablename__ = 'user_learning_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), default='default_user')
    word_id = Column(Integer, ForeignKey('vocabulary.id'), nullable=False)
    learned_at = Column(DateTime, default=func.now())
    confidence_level = Column(Integer, default=1)
    review_count = Column(Integer, default=0)
    last_reviewed = Column(DateTime)

    # Relationships
    vocabulary_word = relationship("Vocabulary", back_populates="learning_progress")

    __table_args__ = (
        UniqueConstraint('user_id', 'word_id'),
        Index('idx_user_progress_user', 'user_id'),
        Index('idx_ulp_word_id', 'word_id'),
        Index('idx_ulp_confidence', confidence_level.desc()),
        Index('idx_ulp_last_reviewed', 'last_reviewed'),
        Index('idx_ulp_review_count', review_count.desc()),
    )


class ProcessingSession(Base):
    """Processing Sessions Table"""
    __tablename__ = 'processing_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False)
    content_type = Column(String(50))
    content_path = Column(String(500))
    total_words = Column(Integer)
    unknown_words_found = Column(Integer)
    processing_time_seconds = Column(Float)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    word_discoveries = relationship("SessionWordDiscovery", back_populates="processing_session")

    __table_args__ = (
        Index('idx_sessions_type', 'content_type'),
        Index('idx_sessions_start_time', 'created_at'),
    )


class SessionWordDiscovery(Base):
    """Session Word Discoveries Table"""
    __tablename__ = 'session_word_discoveries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), ForeignKey('processing_sessions.session_id'), nullable=False)
    word_id = Column(Integer, ForeignKey('vocabulary.id'), nullable=True)
    word = Column(String(100), nullable=False)
    frequency_in_session = Column(Integer, default=1)
    context_examples = Column(Text)

    # Relationships
    processing_session = relationship("ProcessingSession", back_populates="word_discoveries")
    vocabulary_word = relationship("Vocabulary", back_populates="word_discoveries")

    __table_args__ = (
        Index('idx_session_discoveries_session', 'session_id'),
        Index('idx_swd_word', 'word'),
    )


class UserSession(Base):
    """User Sessions Table"""
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    session_token = Column(String(128), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_used = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    # Note: No relationship defined since FastAPI-Users User model doesn't have sessions relationship

    __table_args__ = (
        Index('idx_sessions_token', 'session_token'),
        Index('idx_sessions_user', 'user_id'),
        Index('idx_user_sessions_user_id', 'user_id'),
        Index('idx_user_sessions_token', 'session_token'),
        Index('idx_user_sessions_expires', 'expires_at'),
        Index('idx_user_sessions_active', 'is_active'),
    )


# Database metadata table
class DatabaseMetadata(Base):
    """Database metadata table"""
    __tablename__ = 'database_metadata'

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
