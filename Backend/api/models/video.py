"""
Video API models
"""
from typing import Optional
from pydantic import BaseModel


class VideoInfo(BaseModel):
    series: str
    season: str
    episode: str
    title: str
    path: str
    has_subtitles: bool
    duration: Optional[float] = None