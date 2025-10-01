"""API Versioning implementation for contract management."""

import re
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.routing import APIRoute
from pydantic import BaseModel


class ApiVersion(str, Enum):
    """Supported API versions."""

    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"


class VersioningStrategy(str, Enum):
    """API versioning strategies."""

    HEADER = "header"
    URL_PATH = "url_path"
    QUERY_PARAM = "query_param"


class VersionInfo(BaseModel):
    """Version information model."""

    version: str
    deprecated: bool = False
    sunset_date: str | None = None
    description: str | None = None
    breaking_changes: list[str] = []


class ApiVersionManager:
    """Manages API versioning and compatibility."""

    def __init__(self):
        self.versions: dict[str, VersionInfo] = {
            ApiVersion.V1_0: VersionInfo(
                version="1.0", description="Initial API version with basic auth and video features", deprecated=False
            ),
            ApiVersion.V1_1: VersionInfo(
                version="1.1", description="Enhanced API with improved error handling", deprecated=False
            ),
            ApiVersion.V2_0: VersionInfo(
                version="2.0",
                description="Major API revision with breaking changes",
                deprecated=False,
                breaking_changes=[
                    "Changed authentication response format",
                    "Updated error response structure",
                    "Modified user profile fields",
                ],
            ),
        }
        self.default_version = ApiVersion.V1_0
        self.latest_version = ApiVersion.V2_0

    def get_version_from_request(self, request: Request) -> str:
        """Extract API version from request."""
        # Try header first (preferred method)
        version = request.headers.get("X-API-Version")
        if version:
            return self._normalize_version(version)

        # Try Accept header with version
        accept_header = request.headers.get("Accept", "")
        version_match = re.search(r"version=([\d\.]+)", accept_header)
        if version_match:
            return self._normalize_version(version_match.group(1))

        # Try query parameter
        version = request.query_params.get("version")
        if version:
            return self._normalize_version(version)

        # Try URL path
        path = str(request.url.path)
        version_match = re.search(r"/v([\d\.]+)/", path)
        if version_match:
            return self._normalize_version(version_match.group(1))

        # Return default version
        return self.default_version

    def _normalize_version(self, version: str) -> str:
        """Normalize version string to standard format."""
        # Remove 'v' prefix if present
        version = version.lstrip("v")

        # Ensure major.minor format
        if "." not in version:
            version = f"{version}.0"

        return version

    def validate_version(self, version: str) -> bool:
        """Check if version is supported."""
        return version in self.versions

    def get_version_info(self, version: str) -> VersionInfo | None:
        """Get information about a specific version."""
        return self.versions.get(version)

    def is_version_deprecated(self, version: str) -> bool:
        """Check if version is deprecated."""
        version_info = self.get_version_info(version)
        return version_info.deprecated if version_info else False

    def get_supported_versions(self) -> list[str]:
        """Get list of all supported versions."""
        return list(self.versions.keys())

    def get_latest_version(self) -> str:
        """Get the latest API version."""
        return self.latest_version


# Global version manager instance
version_manager = ApiVersionManager()


def get_api_version(request: Request) -> str:
    """Get API version from request."""
    version = version_manager.get_version_from_request(request)

    if not version_manager.validate_version(version):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "unsupported_api_version",
                "message": f"API version '{version}' is not supported",
                "supported_versions": version_manager.get_supported_versions(),
                "latest_version": version_manager.get_latest_version(),
            },
        )

    return version


def add_version_headers(response, version: str) -> None:
    """Add version-related headers to response."""
    response.headers["X-API-Version"] = version
    response.headers["X-API-Latest-Version"] = version_manager.get_latest_version()

    # Add deprecation warning if needed
    if version_manager.is_version_deprecated(version):
        version_info = version_manager.get_version_info(version)
        response.headers["Deprecation"] = "true"
        if version_info and version_info.sunset_date:
            response.headers["Sunset"] = version_info.sunset_date
        response.headers["Link"] = f'<{version_manager.get_latest_version()}>; rel="successor-version"'


class VersionedRoute(APIRoute):
    """Custom route class that handles API versioning."""

    def __init__(self, *args, **kwargs):
        self.min_version = kwargs.pop("min_version", ApiVersion.V1_0)
        self.max_version = kwargs.pop("max_version", None)
        super().__init__(*args, **kwargs)

    def matches(self, scope: dict[str, Any]) -> tuple:
        """Check if route matches the request including version compatibility."""
        match, child_scope = super().matches(scope)

        if not match:
            return match, child_scope

        # Check version compatibility
        request = Request(scope)
        try:
            version = get_api_version(request)

            # Check minimum version
            if self._compare_versions(version, self.min_version) < 0:
                return False, {}

            # Check maximum version if specified
            if self.max_version and self._compare_versions(version, self.max_version) > 0:
                return False, {}

            return match, child_scope

        except HTTPException:
            return False, {}

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings. Returns -1, 0, or 1."""
        v1_parts = [int(x) for x in v1.split(".")]
        v2_parts = [int(x) for x in v2.split(".")]

        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))

        for i in range(max_len):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1

        return 0


def versioned_endpoint(min_version: str = ApiVersion.V1_0, max_version: str | None = None):
    """Decorator for versioned endpoints."""

    def decorator(func):
        func._min_version = min_version
        func._max_version = max_version
        return func

    return decorator


# Contract validation helpers
def validate_request_contract(request_data: dict[str, Any], version: str) -> dict[str, Any]:
    """Validate request data against version-specific contract."""
    # This would contain version-specific validation logic
    # For now, return the data as-is
    return request_data


def format_response_contract(response_data: dict[str, Any], version: str) -> dict[str, Any]:
    """Format response data according to version-specific contract."""
    # Version-specific response formatting
    if version == ApiVersion.V1_0:
        # V1.0 format - legacy format
        return response_data
    elif version == ApiVersion.V1_1:
        # V1.1 format - enhanced error handling
        if "error" in response_data:
            response_data["error_code"] = response_data.get("error", "unknown_error")
        return response_data
    elif version == ApiVersion.V2_0:
        # V2.0 format - new structure
        if "user" in response_data:
            user_data = response_data["user"]
            # Transform user data for v2.0
            if "created_at" in user_data:
                user_data["created_timestamp"] = user_data["created_at"]
        return response_data

    return response_data
