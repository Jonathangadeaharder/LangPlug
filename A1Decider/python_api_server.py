#!/usr/bin/env python3
"""
FastAPI server for subtitle processing.

This server provides a RESTful API for the unified subtitle processor,
replacing the direct child_process integration with a formal HTTP API.
"""

import os
import sys
import asyncio
import tempfile
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from enum import Enum
import uvicorn

# Import centralized configuration
from config import (
    get_config,
    get_api_config
)
# Add parent directory to path for shared_utils import
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_utils.subtitle_utils import load_word_list

# Import our processing pipeline
from processing_steps import ProcessingContext, ProcessingPipeline
from concrete_processing_steps import (
    PreviewTranscriptionStep,
    FullTranscriptionStep,
    A1FilterStep,
    TranslationStep,
    PreviewProcessingStep
)
from shared_utils.model_utils import ModelManager

# Error Response Schema
class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""
    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"

class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = Field(None, description="Field name that caused the error (for validation errors)")
    message: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(None, description="Specific error code for this detail")

class StandardErrorResponse(BaseModel):
    """Standardized error response format for all API endpoints."""
    success: bool = Field(False, description="Always false for error responses")
    error: ErrorCode = Field(..., description="Primary error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the error")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracking")
    documentation_url: Optional[str] = Field(None, description="Link to relevant documentation")

class ValidationErrorResponse(StandardErrorResponse):
    """Specialized error response for validation errors."""
    error: ErrorCode = Field(ErrorCode.VALIDATION_ERROR, description="Validation error code")
    invalid_fields: List[str] = Field(..., description="List of fields that failed validation")

# Error Handling Utilities
def create_error_response(
    error_code: ErrorCode,
    message: str,
    details: Optional[List[ErrorDetail]] = None,
    status_code: int = 500,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a standardized error response."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    error_response = StandardErrorResponse(
        error=error_code,
        message=message,
        details=details or [],
        timestamp=datetime.now(timezone.utc).isoformat(),
        request_id=request_id,
        documentation_url="https://api-docs.example.com/errors" if error_code != ErrorCode.INTERNAL_ERROR else None
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict()
    )

def create_validation_error_response(
    message: str,
    invalid_fields: List[str],
    details: Optional[List[ErrorDetail]] = None
) -> JSONResponse:
    """Create a validation error response."""
    error_response = ValidationErrorResponse(
        message=message,
        details=details or [],
        timestamp=datetime.now(timezone.utc).isoformat(),
        request_id=str(uuid.uuid4()),
        invalid_fields=invalid_fields,
        documentation_url="https://api-docs.example.com/validation"
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )

def handle_http_exception(exc: HTTPException) -> JSONResponse:
    """Convert HTTPException to standardized error response."""
    # Map HTTP status codes to error codes
    status_to_error_code = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.FILE_NOT_FOUND,
        413: ErrorCode.FILE_TOO_LARGE,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMITED,
        500: ErrorCode.INTERNAL_ERROR,
        503: ErrorCode.DEPENDENCY_ERROR
    }
    
    error_code = status_to_error_code.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    
    return create_error_response(
        error_code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code
    )

# API Models
class ProcessingOptions(BaseModel):
    """Processing options for subtitle generation."""
    language: str = Field(default="de", description="Source language code")
    src_lang: str = Field(default="de", description="Source language for translation")
    tgt_lang: str = Field(default="es", description="Target language for translation")
    no_preview: bool = Field(default=False, description="Skip preview generation")
    pipeline_config: str = Field(default="full", description="Pipeline configuration: 'quick', 'learning', 'full', 'batch'")

class ProcessingRequest(BaseModel):
    """Legacy request model for subtitle processing (deprecated)."""
    video_file_path: str = Field(..., description="Path to the video file to process (deprecated - use file upload instead)")
    language: str = Field(default="de", description="Source language code")
    src_lang: str = Field(default="de", description="Source language for translation")
    tgt_lang: str = Field(default="es", description="Target language for translation")
    no_preview: bool = Field(default=False, description="Skip preview generation")
    pipeline_config: str = Field(default="full", description="Pipeline configuration: 'quick', 'learning', 'full', 'batch'")

class ProcessingResponse(BaseModel):
    """Response model for subtitle processing."""
    success: bool
    message: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    dependencies: Dict[str, bool]

# Get configuration
config = get_config()
api_config = get_api_config()

# Initialize FastAPI app
app = FastAPI(
    title="Subtitle Processing API",
    description="""RESTful API for video subtitle processing with transcription, filtering, and translation.
    
    ## Features
    - **File Upload Processing**: Upload video files directly using multipart/form-data
    - **Multiple Pipeline Configurations**: Quick, Learning, Batch, and Full processing modes
    - **Multi-language Support**: Transcription and translation for multiple languages
    - **A1 Vocabulary Filtering**: Filter subtitles based on A1-level vocabulary
    - **Concurrent Processing**: Thread-safe model management for high performance
    
    ## Primary Endpoint
    Use `/api/process` with file upload (multipart/form-data) for all new integrations.
    
    ## Legacy Support
    File path-based endpoints are deprecated but still available for backward compatibility.
    """,
    version="2.0.0",
    contact={
        "name": "Subtitle Processing API",
        "url": "https://github.com/your-repo/subtitle-processor"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standardized error format."""
    return handle_http_exception(exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with standardized format."""
    details = []
    invalid_fields = []
    
    for error in exc.errors():
        field_name = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body' prefix
        invalid_fields.append(field_name)
        details.append(ErrorDetail(
            field=field_name,
            message=error["msg"],
            code=error["type"]
        ))
    
    return create_validation_error_response(
        message="Request validation failed",
        invalid_fields=invalid_fields,
        details=details
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with standardized error format."""
    return create_error_response(
        error_code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred",
        details=[ErrorDetail(
            message=str(exc),
            code="UNEXPECTED_ERROR"
        )],
        status_code=500
    )

# Global model manager
model_manager = None

def get_model_manager() -> ModelManager:
    """Get or create the global model manager."""
    global model_manager
    if model_manager is None:
        model_manager = ModelManager()
    return model_manager

def create_processing_pipeline(config: str) -> ProcessingPipeline:
    """Create a processing pipeline based on configuration."""
    if config == "quick":
        steps = [FullTranscriptionStep()]
    elif config == "learning":
        steps = [FullTranscriptionStep(), A1FilterStep()]
    elif config == "batch":
        steps = [FullTranscriptionStep(), A1FilterStep(), TranslationStep()]
    elif config == "full":
        steps = [
            PreviewTranscriptionStep(),
            PreviewProcessingStep(),
            FullTranscriptionStep(),
            A1FilterStep(),
            TranslationStep()
        ]
    else:
        raise ValueError(f"Unknown pipeline configuration: {config}")
    
    return ProcessingPipeline(steps)

def check_dependencies() -> Dict[str, bool]:
    """Check if all required dependencies are available."""
    dependencies = {}
    
    try:
        import whisper
        dependencies["whisper"] = True
    except ImportError:
        dependencies["whisper"] = False
    
    try:
        import spacy
        dependencies["spacy"] = True
    except ImportError:
        dependencies["spacy"] = False
    
    try:
        import torch
        dependencies["torch"] = True
    except ImportError:
        dependencies["torch"] = False
    
    try:
        from moviepy.editor import VideoFileClip
        dependencies["moviepy"] = True
    except ImportError:
        dependencies["moviepy"] = False
    
    # Check for required files using centralized configuration
    config = get_config()
    dependencies["a1_files"] = all([
        os.path.exists(config.word_lists.a1_words),
        os.path.exists(config.word_lists.charaktere_words),
        os.path.exists(config.word_lists.giuliwords)
    ])
    
    return dependencies

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    dependencies = check_dependencies()
    
    return HealthResponse(
        status="healthy" if all(dependencies.values()) else "degraded",
        version="1.0.0",
        dependencies=dependencies
    )

@app.get("/api/model-stats", responses={
    500: {"model": StandardErrorResponse, "description": "Model statistics retrieval failed"}
})
async def get_model_stats():
    """Get current model usage statistics for monitoring."""
    try:
        manager = get_model_manager()
        stats = manager.get_model_usage_stats()
        return JSONResponse(content={
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return create_error_response(
            error_code=ErrorCode.MODEL_ERROR,
            message="Failed to retrieve model statistics",
            details=[ErrorDetail(
                message=str(e),
                code="MODEL_STATS_ERROR"
            )],
            status_code=500
        )

async def _process_video_file(video_file_path: str, options: ProcessingOptions) -> ProcessingResponse:
    """Internal function to process a video file."""
    try:
        # Validate video file exists
        if not os.path.exists(video_file_path):
            raise HTTPException(status_code=400, detail=f"Video file not found: {video_file_path}")
        
        # Get model manager
        manager = get_model_manager()
        
        # Load centralized configuration
        config = get_config()
        
        # Load known words from centralized configuration
        known_words = set()
        for word_file in config.word_lists.get_core_files():
            if os.path.exists(word_file):
                words = load_word_list(word_file)
                known_words.update(words)
        
        # Create processing context with configuration data
        context = ProcessingContext(
            video_file=video_file_path,
            model_manager=manager,
            language=options.language,
            src_lang=options.src_lang,
            tgt_lang=options.tgt_lang,
            no_preview=options.no_preview,
            known_words=known_words,
            word_list_files={
                'a1_words': config.word_lists.a1_words,
                'charaktere_words': config.word_lists.charaktere_words,
                'giuliwords': config.word_lists.giuliwords,
                'brands': config.word_lists.brands,
                'onomatopoeia': config.word_lists.onomatopoeia,
                'interjections': config.word_lists.interjections
            },
            processing_config={
                'batch_size': config.processing.batch_size,
                'default_language': config.processing.default_language,
                'supported_languages': config.processing.supported_languages,
                'subtitle_formats': config.processing.subtitle_formats
            }
        )
        
        # Create and execute pipeline
        pipeline = create_processing_pipeline(options.pipeline_config)
        success = pipeline.execute(context)
        
        if success:
            # Prepare results
            results = {
                "video_file": context.video_file,
                "audio_file": context.audio_file,
                "preview_srt": context.preview_srt,
                "full_srt": context.full_srt,
                "filtered_srt": context.filtered_srt,
                "translated_srt": context.translated_srt,
                "metadata": context.metadata
            }
            
            return ProcessingResponse(
                success=True,
                message="Subtitle processing completed successfully",
                results=results
            )
        else:
            return create_error_response(
                error_code=ErrorCode.PROCESSING_ERROR,
                message="Pipeline execution failed",
                details=[ErrorDetail(
                    message="The processing pipeline failed to complete successfully",
                    code="PIPELINE_EXECUTION_FAILED"
                )],
                status_code=500
            )
            
    except Exception as e:
        return create_error_response(
            error_code=ErrorCode.PROCESSING_ERROR,
            message="Subtitle processing failed",
            details=[ErrorDetail(
                message=str(e),
                code="PROCESSING_FAILED"
            )],
            status_code=500
        )
    finally:
        # Cleanup CUDA memory
        global model_manager
        if model_manager:
            model_manager.cleanup_cuda_memory()

def _validate_video_file(file: UploadFile) -> None:
    """Validate uploaded video file."""
    # Check file size (limit to 500MB)
    max_size = 500 * 1024 * 1024  # 500MB
    if hasattr(file, 'size') and file.size and file.size > max_size:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 500MB.")
    
    # Check file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    
    allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format: {file_ext}. Allowed formats: {', '.join(allowed_extensions)}"
        )

@app.post("/api/process", response_model=ProcessingResponse, responses={
    400: {"model": ValidationErrorResponse, "description": "Invalid file or parameters"},
    413: {"model": StandardErrorResponse, "description": "File too large"},
    422: {"model": ValidationErrorResponse, "description": "Request validation failed"},
    500: {"model": StandardErrorResponse, "description": "Processing failed"}
})
async def process_video_upload(
    file: UploadFile = File(..., description="Video file to process"),
    language: str = Form("de", description="Source language code"),
    src_lang: str = Form("de", description="Source language for translation"),
    tgt_lang: str = Form("es", description="Target language for translation"),
    no_preview: bool = Form(False, description="Skip preview generation"),
    pipeline_config: str = Form("full", description="Pipeline configuration")
):
    """Process uploaded video file to generate subtitles (primary endpoint)."""
    try:
        # Validate uploaded file
        _validate_video_file(file)
        
        # Create temporary directory for uploaded file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded file with original filename
            file_path = os.path.join(temp_dir, file.filename)
            
            # Write file content
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Create processing options
            options = ProcessingOptions(
                language=language,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                no_preview=no_preview,
                pipeline_config=pipeline_config
            )
            
            # Process the file
            return await _process_video_file(file_path, options)
            
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response(
            error_code=ErrorCode.PROCESSING_ERROR,
            message="Video upload and processing failed",
            details=[ErrorDetail(
                message=str(e),
                code="UPLOAD_PROCESSING_FAILED"
            )],
            status_code=500
        )

@app.post("/api/process-legacy", response_model=ProcessingResponse, deprecated=True, responses={
    400: {"model": StandardErrorResponse, "description": "Invalid request parameters"},
    404: {"model": StandardErrorResponse, "description": "Video file not found"},
    500: {"model": StandardErrorResponse, "description": "Processing failed"}
})
async def process_subtitles_legacy(request: ProcessingRequest):
    """Process video file using file path (deprecated - use /api/process with file upload instead)."""
    try:
        # Create processing options from legacy request
        options = ProcessingOptions(
            language=request.language,
            src_lang=request.src_lang,
            tgt_lang=request.tgt_lang,
            no_preview=request.no_preview,
            pipeline_config=request.pipeline_config
        )
        
        # Process using the internal function
        return await _process_video_file(request.video_file_path, options)
        
    except Exception as e:
        return create_error_response(
            error_code=ErrorCode.PROCESSING_ERROR,
            message="Legacy subtitle processing failed",
            details=[ErrorDetail(
                message=str(e),
                code="LEGACY_PROCESSING_FAILED"
            )],
            status_code=500
        )

@app.post("/api/upload-and-process", deprecated=True)
async def upload_and_process(
    file: UploadFile = File(...),
    language: str = Form("de"),
    src_lang: str = Form("de"),
    tgt_lang: str = Form("es"),
    no_preview: bool = Form(False),
    pipeline_config: str = Form("full")
):
    """Upload a video file and process it (deprecated - use /api/process instead)."""
    # Redirect to the new primary endpoint
    return await process_video_upload(
        file=file,
        language=language,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
        no_preview=no_preview,
        pipeline_config=pipeline_config
    )

@app.get("/api/download/{file_type}", responses={
    400: {"model": StandardErrorResponse, "description": "Invalid file type or missing parameters"},
    404: {"model": StandardErrorResponse, "description": "Subtitle file not found"},
    500: {"model": StandardErrorResponse, "description": "Download failed"}
})
async def download_subtitle_file(file_type: str, video_path: str = None, session_id: str = None):
    """Download generated subtitle files.
    
    Args:
        file_type: Type of subtitle file (preview, full, filtered, translated)
        video_path: Original video file path (legacy parameter)
        session_id: Processing session ID (future enhancement)
    """
    try:
        if not video_path:
            raise HTTPException(status_code=400, detail="video_path parameter is required")
            
        base_path = os.path.splitext(video_path)[0]
        
        file_mapping = {
            "preview": f"{base_path}_preview.srt",
            "full": f"{base_path}.srt",
            "filtered": f"{base_path}_filtered.srt",
            "translated": f"{base_path}_translated.srt"
        }
        
        if file_type not in file_mapping:
            valid_types = ", ".join(file_mapping.keys())
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file_type}. Valid types: {valid_types}")
        
        file_path = file_mapping[file_type]
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Subtitle file not found: {file_type}. Make sure the video has been processed.")
        
        # Determine appropriate filename for download
        original_name = os.path.splitext(os.path.basename(video_path))[0]
        download_filename = f"{original_name}_{file_type}.srt" if file_type != "full" else f"{original_name}.srt"
        
        return FileResponse(
            path=file_path,
            filename=download_filename,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={download_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/api/pipelines")
async def get_available_pipelines():
    """Get available pipeline configurations."""
    return {
        "pipelines": {
            "quick": {
                "name": "Quick Transcription",
                "description": "Fast transcription only, no filtering or translation",
                "steps": ["transcription"]
            },
            "learning": {
                "name": "Language Learning",
                "description": "Transcription with A1 vocabulary filtering",
                "steps": ["transcription", "filtering"]
            },
            "batch": {
                "name": "Batch Processing",
                "description": "Optimized for processing multiple videos",
                "steps": ["transcription", "filtering", "translation"]
            },
            "full": {
                "name": "Full Processing",
                "description": "Complete pipeline with preview, filtering, and translation",
                "steps": ["preview", "transcription", "filtering", "translation"]
            }
        }
    }

@app.get("/api/upload-info")
async def get_upload_info():
    """Get information about file upload requirements and limits."""
    return {
        "max_file_size": "500MB",
        "max_file_size_bytes": 500 * 1024 * 1024,
        "supported_formats": [
            ".mp4", ".avi", ".mov", ".mkv", 
            ".wmv", ".flv", ".webm", ".m4v"
        ],
        "upload_method": "multipart/form-data",
        "primary_endpoint": "/api/process",
        "legacy_endpoints": {
            "/api/process-legacy": "File path based processing (deprecated)",
            "/api/upload-and-process": "Alternative upload endpoint (deprecated)"
        },
        "supported_languages": {
            "source": ["de", "en", "es", "fr", "it"],
            "translation": ["de", "en", "es", "fr", "it"]
        }
    }

@app.get("/api/formats")
async def get_supported_formats():
    """Get supported video formats and processing options."""
    return {
        "video_formats": {
            "mp4": {"description": "MPEG-4 Video", "recommended": True},
            "avi": {"description": "Audio Video Interleave", "recommended": False},
            "mov": {"description": "QuickTime Movie", "recommended": True},
            "mkv": {"description": "Matroska Video", "recommended": True},
            "wmv": {"description": "Windows Media Video", "recommended": False},
            "flv": {"description": "Flash Video", "recommended": False},
            "webm": {"description": "WebM Video", "recommended": True},
            "m4v": {"description": "iTunes Video", "recommended": True}
        },
        "subtitle_formats": {
            "srt": {"description": "SubRip Subtitle", "extension": ".srt"}
        },
        "processing_options": {
            "languages": ["de", "en", "es", "fr", "it"],
            "pipelines": ["quick", "learning", "batch", "full"]
        }
    }

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    print("🚀 Subtitle Processing API starting up...")
    
    # Check dependencies
    deps = check_dependencies()
    print(f"📋 Dependencies check: {deps}")
    
    if not all(deps.values()):
        print("⚠️  Warning: Some dependencies are missing. API may have limited functionality.")
    
    print("✅ Subtitle Processing API ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    global model_manager
    if model_manager:
        print("🧹 Cleaning up models...")
        model_manager.cleanup_all_models()
        model_manager = None
    print("👋 Subtitle Processing API shutdown complete.")

if __name__ == "__main__":
    # Configuration
    host = os.environ.get("API_HOST", "127.0.0.1")
    port = int(os.environ.get("API_PORT", "8000"))
    
    print(f"🌐 Starting Subtitle Processing API on {host}:{port}")
    
    uvicorn.run(
        "python_api_server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )