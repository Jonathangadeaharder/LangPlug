"""
URL builder utility for robust test URLs using FastAPI route names.
This prevents hardcoded paths from going out of sync with actual routes.
"""

from fastapi import FastAPI
from fastapi.routing import APIRoute


class APIUrlBuilder:
    """Build URLs from FastAPI route names to avoid hardcoded paths in tests."""

    def __init__(self, app: FastAPI):
        self.app = app
        self._route_cache = {}
        self._build_route_cache()

    def _build_route_cache(self):
        """Cache route patterns by name for quick lookup."""
        for route in self.app.routes:
            if isinstance(route, APIRoute) and route.name:
                self._route_cache[route.name] = route.path

    def url_for(self, route_name: str, **path_params) -> str:
        """
        Build URL for a route by name with path parameters.

        Args:
            route_name: The name of the route (from @router.get(name="..."))
            **path_params: Path parameters to substitute in the URL

        Returns:
            Complete URL path

        Example:
            url_for("upload_video_to_series", series="MyShow")
            # Returns: "/api/videos/upload/MyShow"
        """
        if route_name not in self._route_cache:
            raise ValueError(f"Route '{route_name}' not found in app routes")

        url_pattern = self._route_cache[route_name]

        # Replace path parameters
        for param_name, param_value in path_params.items():
            placeholder = "{" + param_name + "}"
            if placeholder in url_pattern:
                url_pattern = url_pattern.replace(placeholder, str(param_value))

        return url_pattern

    def api_url(self, route_name: str, **path_params) -> str:
        """
        Build API URL (assumes /api prefix) for a route by name.
        This is a convenience method for API routes.
        """
        base_url = self.url_for(route_name, **path_params)
        # Most routes already include the /api prefix from router inclusion
        return base_url


def get_url_builder(app: FastAPI) -> APIUrlBuilder:
    """Get URL builder instance for an app."""
    return APIUrlBuilder(app)
