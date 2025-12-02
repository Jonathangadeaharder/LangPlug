"""Task and lifecycle dependencies for FastAPI"""

import csv
import os
import subprocess
import sys
from pathlib import Path

from core.config.logging_config import get_logger
from core.language_preferences import SPACY_MODEL_MAP

logger = get_logger(__name__)

# Log separator for startup/shutdown messages
LOG_SEPARATOR = "=" * 60

# Global task progress registry for background tasks
_task_progress_registry: dict = {}

# Global readiness flag - tracks whether services are fully initialized
_services_ready: bool = False


def get_task_progress_registry() -> dict:
    """
    Get task progress registry for background tasks

    Note:
        Returns reference to global registry without caching.
        Previously used @lru_cache which caused test state pollution.
    """
    return _task_progress_registry


def is_services_ready() -> bool:
    """Check if all services are initialized and ready to handle requests"""
    return _services_ready


async def init_services():
    """Initialize all services on startup"""
    global _services_ready

    logger.info(LOG_SEPARATOR)
    logger.info("[STARTUP] Initializing LangPlug services...")
    logger.info(LOG_SEPARATOR)

    try:
        # Step 0: Validate dependencies (non-blocking)
        if os.getenv("TESTING") != "1":
            logger.info("Step 0/6: Validating dependencies...")
            _validate_dependencies()

        # Initialize authentication services
        logger.info("Step 1/6: Initializing authentication services")
        from core.auth.auth_dependencies import init_auth_services

        init_auth_services()
        logger.info("Authentication services initialized")

        # Initialize database tables
        logger.info("Step 2/6: Initializing database")
        from core.database.database import init_db

        await init_db()
        logger.info("Database initialized")

        # Seed vocabulary data if needed
        if os.getenv("TESTING") != "1":
            logger.info("Step 2.5/6: Checking vocabulary data...")
            await _ensure_vocabulary_data()

        # Initialize transcription service
        if os.getenv("TESTING") != "1":
            logger.info("Step 3/6: Initializing transcription service")
            from core.config.config import settings

            from .service_dependencies import get_transcription_service

            logger.info("Using transcription model", model=settings.transcription_service)
            get_transcription_service()
            logger.info("Transcription service ready")

            # Initialize translation service
            logger.info("Step 4/6: Initializing translation service")
            from .service_dependencies import get_translation_service

            logger.info("Using translation model", model=settings.translation_service)
            get_translation_service()
            logger.info("Translation service ready")
        else:
            logger.info("Skipping model initialization in test mode")

        # Initialize task progress registry
        logger.info("Step 5/6: Initializing task registry")
        get_task_progress_registry()

        # Validate spaCy models (non-blocking warning)
        if os.getenv("TESTING") != "1":
            logger.info("Step 6/6: Validating NLP models...")
            _validate_spacy_models()

        # Mark services as ready
        _services_ready = True
        logger.info(LOG_SEPARATOR)
        logger.info("[STARTUP COMPLETE] All services initialized, server ready")
        logger.info(LOG_SEPARATOR)

    except Exception as e:
        _services_ready = False
        logger.error("Failed to initialize services", error=str(e), exc_info=True)
        raise


async def cleanup_services():
    """Cleanup services on shutdown"""
    logger.info("Cleaning up services...")

    # Cleanup authentication services
    from core.auth.auth_dependencies import cleanup_auth_services

    cleanup_auth_services()

    # Close database engine
    from core.database.database import engine

    await engine.dispose()

    # Clear task progress registry content (not cache, as we removed @lru_cache)
    _task_progress_registry.clear()

    logger.info("Service cleanup complete")


def _validate_spacy_models() -> None:
    """Validate that required spaCy models are installed.
    
    Auto-installs missing models if not found. Uses small German model in debug mode.
    """
    from core.config.config import settings

    # Use small German model in debug mode unless explicitly overridden
    model_de = settings.spacy_model_de
    if getattr(settings, "debug", False) and model_de == "de_core_news_lg":
        debug_model_de = SPACY_MODEL_MAP.get("de", "de_core_news_sm")
        logger.info(
            "Using small German spaCy model in debug mode",
            original=model_de,
            debug_model=debug_model_de,
        )
        settings.spacy_model_de = debug_model_de
        model_de = debug_model_de

    # Use a local variable for English as well for consistency
    model_en = settings.spacy_model_en

    required_models = [
        ("de", model_de),
        ("en", model_en),
    ]

    missing_models = []

    try:
        import spacy
    except ImportError:
        logger.info("[AUTO-INSTALL] Installing spaCy...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "spacy"],
                check=True,
                capture_output=True,
                text=True,
            )
            import spacy
            logger.info("[AUTO-INSTALL] spaCy installed successfully")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"[FATAL] Failed to install spaCy: {e.stderr}. "
                "Run: pip install spacy"
            )

    for lang, model_name in required_models:
        try:
            spacy.load(model_name)
            logger.info("spaCy model loaded successfully", model=model_name, language=lang)
        except OSError:
            missing_models.append(model_name)

    if missing_models:
        logger.info(f"[AUTO-INSTALL] Installing spaCy models: {missing_models}")
        for model in missing_models:
            try:
                logger.info(f"[AUTO-INSTALL] Downloading {model}...")
                subprocess.run(
                    [sys.executable, "-m", "spacy", "download", model],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )
                logger.info(f"[AUTO-INSTALL] {model} installed successfully")
            except subprocess.TimeoutExpired:
                raise RuntimeError(
                    f"[FATAL] Timeout downloading {model}. "
                    f"Run: python -m spacy download {model}"
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"[FATAL] Failed to download {model}: {e.stderr}. "
                    f"Run: python -m spacy download {model}"
                )
        # Verify installation
        for lang, model_name in required_models:
            try:
                spacy.load(model_name)
                logger.info("spaCy model loaded successfully", model=model_name, language=lang)
            except OSError:
                raise RuntimeError(
                    f"[FATAL] Failed to load {model_name} after installation. "
                    f"Run: python -m spacy download {model_name}"
                )

    logger.info("All spaCy models validated successfully")


def _validate_dependencies() -> None:
    """Validate that required Python dependencies are installed.
    
    Auto-installs missing packages if not found.
    """
    required_packages = [
        ("spacy", "spaCy NLP library for vocabulary processing"),
        ("faster_whisper", "Whisper transcription"),
        ("transformers", "Translation models"),
        ("torch", "PyTorch for ML models"),
    ]
    
    missing = []
    for package, description in required_packages:
        try:
            __import__(package)
            logger.debug("Dependency OK", package=package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.info(f"[AUTO-INSTALL] Installing missing packages: {missing}")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install"] + missing,
                check=True,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )
            logger.info(f"[AUTO-INSTALL] Packages installed: {missing}")
            # Verify installation
            for package in missing:
                __import__(package)
            logger.info("All packages verified after installation")
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"[FATAL] Timeout installing packages: {missing}. "
                f"Run: pip install {' '.join(missing)}"
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"[FATAL] Failed to install packages: {missing}. "
                f"Error: {e.stderr}. Run: pip install {' '.join(missing)}"
            )
    
    logger.info("All Python dependencies validated")


async def _ensure_vocabulary_data() -> None:
    """Ensure vocabulary database is populated with word difficulty data.
    
    Checks if vocabulary_words table has data and imports from CSV files if empty.
    Raises RuntimeError if vocabulary cannot be seeded.
    """
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError
    from core.database.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        # Check current vocabulary count (handle case where table doesn't exist)
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM vocabulary_words WHERE language = 'de'")
            )
            count = result.scalar() or 0
        except OperationalError:
            # Table doesn't exist yet - this is a bug, init_db should have created it
            raise RuntimeError(
                "[FATAL] vocabulary_words table not found. Database initialization failed."
            )
        
        if count > 0:
            logger.info("Vocabulary data present", word_count=count)
            return
        
        logger.info("Vocabulary empty - seeding from CSV files...")
        
        # Find CSV files in data directory
        backend_root = Path(__file__).parent.parent.parent
        data_dir = backend_root / "data"
        
        if not data_dir.exists():
            raise RuntimeError(
                f"[FATAL] Data directory not found: {data_dir}. "
                "Cannot seed vocabulary data."
            )
        
        csv_files = {
            "A1_vokabeln.csv": "A1",
            "A2_vokabeln.csv": "A2",
            "B1_vokabeln.csv": "B1",
            "B2_vokabeln.csv": "B2",
            "C1_vokabeln.csv": "C1",
        }
        
        total_imported = 0
        
        for csv_file, level in csv_files.items():
            csv_path = data_dir / csv_file
            if not csv_path.exists():
                logger.debug("CSV file not found", file=csv_file)
                continue
                candidate_words = []
                for row in reader:
                    if len(row) >= 2 and row[0].strip() and row[1].strip():
                        german = row[0].strip()
                        spanish = row[1].strip()
                        candidate_words.append((german, spanish))

                # Query all existing words for this language and level
                if candidate_words:
                    german_words = [w[0] for w in candidate_words]
                    existing_result = await session.execute(
                        text("""
                            SELECT word FROM vocabulary_words
                            WHERE word IN :words AND language = :lang
                        """),
                        {"words": tuple(german_words), "lang": "de"},
                    )
                    existing_words = set(row[0] for row in existing_result.fetchall())
                else:
                    existing_words = set()

                # Prepare new words to insert
                new_word_dicts = []
                for german, spanish in candidate_words:
                    if german not in existing_words:
                        new_word_dicts.append({
                            "word": german,
                            "lemma": german.lower(),
                            "language": "de",
                            "difficulty_level": level,
                            "translation_native": spanish,
                        })

                if new_word_dicts:
                    await session.execute(
                        text("""
                            INSERT INTO vocabulary_words
                            (word, lemma, language, difficulty_level, translation_native, created_at, updated_at)
                            VALUES
                            """ +
                            ", ".join(
                                f"(:word{i}, :lemma{i}, :language{i}, :difficulty_level{i}, :translation_native{i}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                                for i in range(len(new_word_dicts))
                            )
                        ),
                        {
                            **{
                                f"word{i}": d["word"] for i, d in enumerate(new_word_dicts)
                            },
                            **{
                                f"lemma{i}": d["lemma"] for i, d in enumerate(new_word_dicts)
                            },
                            **{
                                f"language{i}": d["language"] for i, d in enumerate(new_word_dicts)
                            },
                            **{
                                f"difficulty_level{i}": d["difficulty_level"] for i, d in enumerate(new_word_dicts)
                            },
                            **{
                                f"translation_native{i}": d["translation_native"] for i, d in enumerate(new_word_dicts)
                            },
                        }
                    )
                    total_imported += len(new_word_dicts)
                            )
                            total_imported += 1
            
            logger.info("Imported vocabulary from CSV", file=csv_file, level=level)
        
        if total_imported > 0:
            await session.commit()
            logger.info("Vocabulary seeded", total_words=total_imported)
        else:
            raise RuntimeError(
                f"[FATAL] No vocabulary imported. CSV files missing or empty in {data_dir}. "
                "Required files: A1_vokabeln.csv, A2_vokabeln.csv, B1_vokabeln.csv, B2_vokabeln.csv, C1_vokabeln.csv"
            )


__all__ = ["cleanup_services", "get_task_progress_registry", "init_services", "is_services_ready"]
