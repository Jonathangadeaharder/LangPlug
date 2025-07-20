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
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
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

# API Models
class ProcessingRequest(BaseModel):
    """Request model for subtitle processing."""
    video_file_path: str = Field(..., description="Path to the video file to process")
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
    description="RESTful API for video subtitle processing with transcription, filtering, and translation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.post("/api/process", response_model=ProcessingResponse)
async def process_subtitles(request: ProcessingRequest):
    """Process video file to generate subtitles."""
    try:
        # Validate video file exists
        if not os.path.exists(request.video_file_path):
            raise HTTPException(status_code=400, detail=f"Video file not found: {request.video_file_path}")
        
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
            video_file=request.video_file_path,
            model_manager=manager,
            language=request.language,
            src_lang=request.src_lang,
            tgt_lang=request.tgt_lang,
            no_preview=request.no_preview,
            known_words=known_words,
            word_list_files={
                'a1_words': config.word_lists.a1_words,
                'charaktere_words': config.word_lists.charaktere_words,
                'giuliwords': config.word_lists.giuliwords,
                'brands': config.word_lists.brands,
                'onomatopoeia': config.word_lists.onomatopoeia,
                'interjections': config.word_lists.interjections
            }
            processing_config={
                'batch_size': config.processing.batch_size,
                'default_language': config.processing.default_language,
                'supported_languages': config.processing.supported_languages,
                'subtitle_formats': config.processing.subtitle_formats
            }
        )
        
        # Create and execute pipeline
        pipeline = create_processing_pipeline(request.pipeline_config)
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
            return ProcessingResponse(
                success=False,
                message="Subtitle processing failed",
                error="Pipeline execution failed"
            )
            
    except Exception as e:
        return ProcessingResponse(
            success=False,
            message="Subtitle processing failed",
            error=str(e)
        )
    finally:
        # Cleanup CUDA memory
        if model_manager:
            model_manager.cleanup_cuda_memory()

@app.post("/api/upload-and-process")
async def upload_and_process(
    file: UploadFile = File(...),
    language: str = Form("de"),
    src_lang: str = Form("de"),
    tgt_lang: str = Form("es"),
    no_preview: bool = Form(False),
    pipeline_config: str = Form("full")
):
    """Upload a video file and process it."""
    try:
        # Create temporary directory for uploaded file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded file
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Create processing request
            request = ProcessingRequest(
                video_file_path=file_path,
                language=language,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                no_preview=no_preview,
                pipeline_config=pipeline_config
            )
            
            # Process the file (this will use centralized configuration)
            response = await process_subtitles(request)
            return response
            
    except Exception as e:
        return ProcessingResponse(
            success=False,
            message="Upload and processing failed",
            error=str(e)
        )

@app.get("/api/download/{file_type}")
async def download_subtitle_file(file_type: str, video_path: str):
    """Download generated subtitle files."""
    try:
        base_path = os.path.splitext(video_path)[0]
        
        file_mapping = {
            "preview": f"{base_path}_preview.srt",
            "full": f"{base_path}.srt",
            "filtered": f"{base_path}_filtered.srt",
            "translated": f"{base_path}_translated.srt"
        }
        
        if file_type not in file_mapping:
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file_type}")
        
        file_path = file_mapping[file_type]
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="text/plain"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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