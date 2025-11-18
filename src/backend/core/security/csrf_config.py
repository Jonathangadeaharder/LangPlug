"""
CSRF Protection Configuration
Requires: pip install fastapi-csrf-protect==0.3.2

To enable CSRF protection:
1. Install: pip install fastapi-csrf-protect==0.3.2
2. Import this module in main.py
3. Add CSRF token endpoint to auth routes
4. Update frontend to include CSRF tokens in state-changing requests

Example usage in main.py:
    from fastapi_csrf_protect import CsrfProtect
    from core.csrf_config import get_csrf_config

    @CsrfProtect.load_config
    def load_csrf_config():
        return get_csrf_config()

    @app.post("/api/auth/csrf-token")
    async def generate_csrf_token(csrf_protect: CsrfProtect = Depends()):
        csrf_protect.set_csrf_cookie()
        return {"message": "CSRF cookie set"}

Example endpoint protection:
    async def endpoint(csrf_protect: CsrfProtect = Depends()):
        csrf_protect.validate_csrf()
        # ... rest of endpoint
"""

from pydantic import BaseModel

from core.config import settings


class CsrfSettings(BaseModel):
    """CSRF protection settings"""

    secret_key: str = settings.secret_key
    cookie_name: str = "fastapi-csrf-token"
    cookie_path: str = "/"
    cookie_domain: str | None = None
    cookie_secure: bool = settings.environment == "production"  # HTTPS only in production
    cookie_samesite: str = "lax"  # Prevents CSRF while allowing some cross-site usage
    cookie_httponly: bool = False  # Must be False so JavaScript can read for inclusion in headers
    header_name: str = "X-CSRF-Token"
    header_type: str | None = None
    token_location: str = "header"  # Token sent in custom header
    token_key: str = "csrf_token"


def get_csrf_config() -> CsrfSettings:
    """Get CSRF configuration"""
    return CsrfSettings()
