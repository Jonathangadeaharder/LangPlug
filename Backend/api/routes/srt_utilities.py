"""
SRT Utilities API Endpoints

This module provides API endpoints for SRT subtitle parsing and manipulation.
This ensures the backend is the single source of truth for SRT processing logic.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from utils.srt_parser import SRTParser, SRTSegment


router = APIRouter(prefix="/api/srt", tags=["SRT Utilities"])


class SRTSegmentResponse(BaseModel):
    """Response model for SRT segment data."""
    index: int
    start_time: float
    end_time: float
    text: str
    original_text: str = ""
    translation: str = ""


class ParseSRTRequest(BaseModel):
    """Request model for parsing SRT content."""
    content: str


class ParseSRTResponse(BaseModel):
    """Response model for parsed SRT data."""
    segments: List[SRTSegmentResponse]
    total_segments: int
    duration: float  # Total duration in seconds


class ConvertToSRTRequest(BaseModel):
    """Request model for converting segments to SRT format."""
    segments: List[SRTSegmentResponse]


@router.post("/parse", response_model=ParseSRTResponse)
async def parse_srt_content(request: ParseSRTRequest):
    """
    Parse SRT content and return structured data.
    
    This endpoint replaces frontend SRT parsing logic, ensuring
    the backend is the single source of truth for SRT processing.
    
    Args:
        request: SRT content to parse
        
    Returns:
        Parsed SRT segments with metadata
        
    Raises:
        HTTPException: If parsing fails
    """
    try:
        # Parse using the backend SRT parser
        segments = SRTParser.parse_content(request.content)
        
        # Convert to response format
        response_segments = []
        max_end_time = 0
        
        for segment in segments:
            response_segments.append(SRTSegmentResponse(
                index=segment.index,
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=segment.text,
                original_text=segment.original_text,
                translation=segment.translation
            ))
            max_end_time = max(max_end_time, segment.end_time)
        
        return ParseSRTResponse(
            segments=response_segments,
            total_segments=len(response_segments),
            duration=max_end_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse SRT content: {str(e)}"
        )


@router.post("/parse-file")
async def parse_srt_file(file: UploadFile = File(...)):
    """
    Parse an uploaded SRT file and return structured data.
    
    Args:
        file: Uploaded SRT file
        
    Returns:
        Parsed SRT segments with metadata
        
    Raises:
        HTTPException: If file processing fails
    """
    if not file.filename or not file.filename.endswith('.srt'):
        raise HTTPException(
            status_code=400,
            detail="File must be an SRT file (.srt extension)"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Decode content (try UTF-8 first, fall back to latin-1)
        try:
            srt_content = content.decode('utf-8')
        except UnicodeDecodeError:
            srt_content = content.decode('latin-1')
        
        # Parse using the existing endpoint logic
        request = ParseSRTRequest(content=srt_content)
        return await parse_srt_content(request)
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process SRT file: {str(e)}"
        )


@router.post("/convert-to-srt")
async def convert_to_srt(request: ConvertToSRTRequest):
    """
    Convert structured segment data back to SRT format.
    
    Args:
        request: Segments to convert
        
    Returns:
        SRT formatted content
        
    Raises:
        HTTPException: If conversion fails
    """
    try:
        # Convert request segments to SRTSegment objects
        segments = []
        for segment_data in request.segments:
            segment = SRTSegment(
                index=segment_data.index,
                start_time=segment_data.start_time,
                end_time=segment_data.end_time,
                text=segment_data.text,
                original_text=segment_data.original_text,
                translation=segment_data.translation
            )
            segments.append(segment)
        
        # Convert to SRT format
        srt_content = SRTParser.segments_to_srt(segments)
        
        # Return as plain text response
        return Response(
            content=srt_content,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=subtitles.srt"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to convert to SRT format: {str(e)}"
        )


@router.get("/validate")
async def validate_srt_content(content: str):
    """
    Validate SRT content without full parsing.
    
    Args:
        content: SRT content to validate
        
    Returns:
        Validation result with issues found
    """
    try:
        segments = SRTParser.parse_content(content)
        
        issues = []
        
        # Check for common issues
        for i, segment in enumerate(segments):
            # Check for overlapping timestamps
            if i > 0 and segment.start_time < segments[i-1].end_time:
                issues.append(f"Segment {segment.index}: Overlaps with previous segment")
            
            # Check for negative duration
            if segment.end_time <= segment.start_time:
                issues.append(f"Segment {segment.index}: Invalid duration")
            
            # Check for missing text
            if not segment.text and not segment.original_text:
                issues.append(f"Segment {segment.index}: Missing text content")
        
        return {
            "valid": len(issues) == 0,
            "total_segments": len(segments),
            "issues": issues
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "issues": ["Failed to parse SRT content"]
        }
