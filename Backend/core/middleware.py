"""
Middleware for FastAPI application
"""
import logging
import time
from datetime import datetime
from typing import Callable
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .exceptions import LangPlugException
from services.authservice.auth_service import (
    InvalidCredentialsError, UserAlreadyExistsError, SessionExpiredError
)


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        api_logger = logging.getLogger("api")
        
        # Don't read request body in middleware - it causes issues with body consumption
        # Just log the request metadata
        
        # Log detailed request information
        api_logger.info(
            f"API Request: {request.method} {request.url.path}",
            extra={
                "event_type": "api_request",
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": {k: v for k, v in request.headers.items() if k.lower() not in ['authorization', 'cookie']},
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Read response body for logging (if it's JSON and not too large)
            response_body = None
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    # For small responses, log the body
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) < 1024 * 10:  # Less than 10KB
                        response_body = "[Response body available but not logged for privacy]"
                except Exception:
                    pass
            
            # Log response
            api_logger.info(
                f"API Response: {response.status_code} {request.method} {request.url.path}",
                extra={
                    "event_type": "api_response",
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4),
                    "response_headers": dict(response.headers),
                    "response_body": response_body,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Add processing time to response headers
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "process_time": round(process_time, 4),
                    "timestamp": datetime.utcnow().isoformat()
                },
                exc_info=True
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # Re-raise HTTP exceptions (handled by FastAPI)
            raise
        except LangPlugException as e:
            # Handle custom application exceptions
            logger.error(f"LangPlug error: {e.message}", exc_info=True)
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "detail": e.message,
                    "type": "LangPlugException",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except InvalidCredentialsError as e:
            logger.warning(f"Invalid credentials: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": str(e),
                    "type": "InvalidCredentialsError",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except UserAlreadyExistsError as e:
            logger.warning(f"User already exists: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": str(e),
                    "type": "UserAlreadyExistsError",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except SessionExpiredError as e:
            logger.warning(f"Session expired: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": str(e),
                    "type": "SessionExpiredError",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "type": "UnexpectedError",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )


def setup_middleware(app: FastAPI) -> None:
    """Set up all middleware for the FastAPI application"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware (order matters - first added runs last)
    # Temporarily disable custom middleware - causing OPTIONS request issues
    # app.add_middleware(ErrorHandlingMiddleware)
    # app.add_middleware(LoggingMiddleware)
    
    # Exception handlers
    @app.exception_handler(LangPlugException)
    async def langplug_exception_handler(request: Request, exc: LangPlugException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "type": exc.__class__.__name__,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    logger.info("Middleware configured successfully")