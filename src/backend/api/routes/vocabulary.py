"""Vocabulary management API routes.

This module aggregates vocabulary routes from focused sub-modules:
- vocabulary_query_routes: Read operations (word-info, library, search, languages)
- vocabulary_progress_routes: Progress tracking (mark-known, stats, bulk-mark)
- vocabulary_test_routes: E2E test endpoints (test-data, blocking-words, create)
"""

import logging

from fastapi import APIRouter

from api.routes.vocabulary_progress_routes import router as progress_router
from api.routes.vocabulary_query_routes import router as query_router
from api.routes.vocabulary_test_routes import router as test_router

logger = logging.getLogger(__name__)

router = APIRouter(tags=["vocabulary"])

router.include_router(query_router)
router.include_router(progress_router)
router.include_router(test_router)

__all__ = ["router"]
