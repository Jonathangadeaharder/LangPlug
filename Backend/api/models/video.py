"""
Video API models
"""

from pydantic import BaseModel, Field, validator


class VideoInfo(BaseModel):
    series: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the TV series"
    )
    season: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Season identifier (e.g., 'S01', 'Season 1')"
    )
    episode: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Episode identifier (e.g., 'E01', 'Episode 1')"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Episode title"
    )
    path: str = Field(
        ...,
        min_length=1,
        description="File system path to the video file"
    )
    has_subtitles: bool = Field(
        ...,
        description="Whether subtitles are available for this video"
    )
    duration: float | None = Field(
        None,
        ge=0,
        description="Video duration in seconds"
    )

    @validator('path')
    def validate_path_format(cls, v):
        if not v.strip():
            raise ValueError('Path cannot be empty or whitespace')
        # Check for common video file extensions
        valid_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
        if not any(v.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f'Path must end with a valid video extension: {", ".join(valid_extensions)}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "series": "Superstore",
                "season": "S01",
                "episode": "E01",
                "title": "Pilot",
                "path": "/videos/Superstore/S01/E01.mp4",
                "has_subtitles": True,
                "duration": 1320.5
            }
        }
