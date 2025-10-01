"""
Monitoring and observability implementation
"""

import json
import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any

import psutil
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class MetricsCollector:
    """Metrics collection and storage"""

    def __init__(self):
        self.metrics: dict[str, Any] = {
            "requests_total": 0,
            "requests_by_method": {},
            "requests_by_endpoint": {},
            "response_times": [],
            "error_counts": {},
            "active_connections": 0,
        }
        self.start_time = time.time()

    def record_request(self, method: str, endpoint: str, response_time: float, status_code: int):
        """Record request metrics"""
        self.metrics["requests_total"] += 1

        # Method counts
        if method not in self.metrics["requests_by_method"]:
            self.metrics["requests_by_method"][method] = 0
        self.metrics["requests_by_method"][method] += 1

        # Endpoint counts
        if endpoint not in self.metrics["requests_by_endpoint"]:
            self.metrics["requests_by_endpoint"][endpoint] = 0
        self.metrics["requests_by_endpoint"][endpoint] += 1

        # Response times (keep last 1000)
        self.metrics["response_times"].append(response_time)
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]

        # Error counts
        if status_code >= 400:
            if status_code not in self.metrics["error_counts"]:
                self.metrics["error_counts"][status_code] = 0
            self.metrics["error_counts"][status_code] += 1

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics"""
        uptime = time.time() - self.start_time
        response_times = self.metrics["response_times"]

        return {
            "uptime_seconds": uptime,
            "requests_total": self.metrics["requests_total"],
            "requests_by_method": self.metrics["requests_by_method"],
            "requests_by_endpoint": self.metrics["requests_by_endpoint"],
            "error_counts": self.metrics["error_counts"],
            "active_connections": self.metrics["active_connections"],
            "response_time_stats": {
                "avg": sum(response_times) / len(response_times) if response_times else 0,
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "count": len(response_times),
            },
            "system": self._get_system_metrics(),
        }

    def _get_system_metrics(self) -> dict[str, Any]:
        """Get system resource metrics"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            cpu_percent = psutil.cpu_percent(interval=1)

            return {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_total_mb": memory.total // (1024 * 1024),
                "memory_available_mb": memory.available // (1024 * 1024),
                "disk_usage_percent": disk.percent,
                "disk_total_gb": disk.total // (1024 * 1024 * 1024),
                "disk_free_gb": disk.free // (1024 * 1024 * 1024),
            }
        except Exception as e:
            return {"error": str(e)}


# Global metrics collector
metrics_collector = MetricsCollector()


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting request metrics"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request.state.start_time = start_time

        # Increment active connections
        metrics_collector.metrics["active_connections"] += 1

        try:
            response = await call_next(request)
            response_time = time.time() - start_time

            # Record metrics
            endpoint = self._get_endpoint(request)
            metrics_collector.record_request(request.method, endpoint, response_time, response.status_code)

            return response

        except Exception:
            # Record error
            response_time = time.time() - start_time
            endpoint = self._get_endpoint(request)
            metrics_collector.record_request(request.method, endpoint, response_time, 500)
            raise

        finally:
            # Decrement active connections
            metrics_collector.metrics["active_connections"] -= 1

    def _get_endpoint(self, request: Request) -> str:
        """Extract endpoint pattern from request"""
        path = request.url.path
        # Normalize paths with IDs (simple approach)
        import re

        path = re.sub(r"/\d+", "/{id}", path)
        path = re.sub(r"/[a-f0-9-]{36}", "/{uuid}", path)
        return path


class PerformanceProfiler:
    """Performance profiling utilities"""

    @staticmethod
    def profile_function(func_name: str | None = None):
        """Decorator to profile function execution time"""

        def decorator(func):
            name = func_name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    logging.info(f"Function {name} executed in {execution_time:.3f}s")

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    logging.info(f"Function {name} executed in {execution_time:.3f}s")

            return async_wrapper if callable(func) and func.__code__.co_flags & 0x80 else sync_wrapper

        return decorator

    @staticmethod
    @contextmanager
    def profile_block(block_name: str):
        """Context manager to profile code blocks"""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            logging.info(f"Block {block_name} executed in {execution_time:.3f}s")


class StructuredLogger:
    """Structured logging with correlation IDs"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str, message: str, extra: dict[str, Any] | None = None, request_id: str | None = None):
        """Log with structured format"""
        log_data = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "request_id": request_id,
        }
        if extra:
            log_data.update(extra)

        getattr(self.logger, level.lower())(json.dumps(log_data))

    def info(self, message: str, extra: dict[str, Any] | None = None, request_id: str | None = None):
        self.log("INFO", message, extra, request_id)

    def error(self, message: str, extra: dict[str, Any] | None = None, request_id: str | None = None):
        self.log("ERROR", message, extra, request_id)

    def warning(self, message: str, extra: dict[str, Any] | None = None, request_id: str | None = None):
        self.log("WARNING", message, extra, request_id)

    def debug(self, message: str, extra: dict[str, Any] | None = None, request_id: str | None = None):
        self.log("DEBUG", message, extra, request_id)


def get_logger(name: str) -> StructuredLogger:
    """Get structured logger instance"""
    return StructuredLogger(name)


# Health check implementations
async def check_database_health() -> dict[str, Any]:
    """Check database health"""
    try:
        from core.database import SessionLocal

        db = SessionLocal()
        start_time = time.time()
        db.execute("SELECT 1")
        response_time = time.time() - start_time
        db.close()

        return {
            "status": "healthy",
            "response_time_ms": round(response_time * 1000, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def check_cache_health() -> dict[str, Any]:
    """Check cache health"""
    try:
        from .caching import cache_manager

        start_time = time.time()
        cache_manager.set("health_check", "test", 10)
        result = cache_manager.get("health_check")
        cache_manager.delete("health_check")
        response_time = time.time() - start_time

        if result == "test":
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
            }
        else:
            return {
                "status": "unhealthy",
                "error": "Cache test failed",
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
