"""
SRT Utilities API Endpoints

This module provides API endpoints for SRT subtitle parsing and manipulation.
This ensures the backend is the single source of truth for SRT processing logic.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

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

    segments: list[SRTSegmentResponse]
    total_segments: int
    duration: float  # Total duration in seconds


class ConvertToSRTRequest(BaseModel):
    """Request model for converting segments to SRT format."""

    segments: list[SRTSegmentResponse]


@router.post("/parse", response_model=ParseSRTResponse)
async def parse_srt_content(request: ParseSRTRequest):
    """
    Parse SRT subtitle content and return structured segment data.

    Converts raw SRT text format into structured JSON with parsed timestamps,
    segment indices, and text content. This endpoint centralizes SRT parsing
    logic on the backend, ensuring consistent parsing across the application.

    **Authentication Required**: No

    Args:
        request (ParseSRTRequest): Request with:
            - content (str): Raw SRT file content

    Returns:
        ParseSRTResponse: Parsed data with:
            - segments: List of subtitle segments
                - index: Segment number
                - start_time: Start timestamp in seconds
                - end_time: End timestamp in seconds
                - text: Subtitle text
                - original_text: Original text (if available)
                - translation: Translation text (if available)
            - total_segments: Total number of segments
            - duration: Total video duration in seconds

    Raises:
        HTTPException: 400 if SRT content is malformed or unparseable

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/srt/parse" \
          -H "Content-Type: application/json" \
          -d '{
            "content": "1\\n00:00:00,000 --> 00:00:05,000\\nHallo!\\n\\n2\\n00:00:05,500 --> 00:00:10,000\\nWie geht es dir?"
          }'
        ```

        Response:
        ```json
        {
            "segments": [
                {
                    "index": 1,
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "text": "Hallo!",
                    "original_text": "",
                    "translation": ""
                },
                {
                    "index": 2,
                    "start_time": 5.5,
                    "end_time": 10.0,
                    "text": "Wie geht es dir?",
                    "original_text": "",
                    "translation": ""
                }
            ],
            "total_segments": 2,
            "duration": 10.0
        }
        ```

    Note:
        This endpoint should be used by frontend instead of client-side SRT parsing
        to ensure consistency and reduce code duplication.
    """
    try:
        segments = SRTParser.parse_content(request.content)

        response_segments = []
        max_end_time = 0

        for segment in segments:
            response_segments.append(
                SRTSegmentResponse(
                    index=segment.index,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    text=segment.text,
                    original_text=segment.original_text,
                    translation=segment.translation,
                )
            )
            max_end_time = max(max_end_time, segment.end_time)

        return ParseSRTResponse(
            segments=response_segments, total_segments=len(response_segments), duration=max_end_time
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse SRT content: {e!s}") from e


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
    if not file.filename or not file.filename.endswith(".srt"):
        raise HTTPException(status_code=400, detail="File must be an SRT file (.srt extension)")

    try:
        content = await file.read()

        try:
            srt_content = content.decode("utf-8")
        except UnicodeDecodeError:
            srt_content = content.decode("latin-1")

        request = ParseSRTRequest(content=srt_content)
        return await parse_srt_content(request)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process SRT file: {e!s}") from e


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
        segments = []
        for segment_data in request.segments:
            segment = SRTSegment(
                index=segment_data.index,
                start_time=segment_data.start_time,
                end_time=segment_data.end_time,
                text=segment_data.text,
                original_text=segment_data.original_text,
                translation=segment_data.translation,
            )
            segments.append(segment)

        srt_content = SRTParser.segments_to_srt(segments)

        return Response(
            content=srt_content,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=subtitles.srt"},
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to convert to SRT format: {e!s}") from e


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

        for i, segment in enumerate(segments):
            if i > 0 and segment.start_time < segments[i - 1].end_time:
                issues.append(f"Segment {segment.index}: Overlaps with previous segment")

            if segment.end_time <= segment.start_time:
                issues.append(f"Segment {segment.index}: Invalid duration")

            if not segment.text and not segment.original_text:
                issues.append(f"Segment {segment.index}: Missing text content")

        return {"valid": len(issues) == 0, "total_segments": len(segments), "issues": issues}

    except Exception as e:
        return {"valid": False, "error": str(e), "issues": ["Failed to parse SRT content"]}
