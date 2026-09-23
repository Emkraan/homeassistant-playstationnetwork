"""Compatibility fixes for the PSNAWP library."""

import json
from typing import Any

from psnawp_api.core import psnawp_exceptions
from psnawp_api.core.psnawp_exceptions import (
    PSNAWPAuthenticationError,
    PSNAWPBadRequestError,
    PSNAWPError,
)

# OAuth error codes Sony returns when the stored refresh token (or npsso) can
# no longer be used, e.g. after a password change, enabling a passkey, or
# signing out of all devices. Only a new npsso token fixes these.
OAUTH_AUTH_ERRORS = {"invalid_grant", "invalid_client", "unauthorized_client"}


def _psnawp_error_init(self: PSNAWPError, response: str) -> None:
    """Parse both PSN API and OAuth error bodies.

    PSNAWP 3.0.3 assumes every error body looks like
    {"error": {"code": ..., "message": ...}}. The OAuth token endpoint instead
    returns {"error": "invalid_grant", "error_description": ...}, so the
    library crashes with "'str' object has no attribute 'get'" while building
    the exception, hiding the real failure.
    """
    self.code = None
    self.message = None
    self.reference_id = None
    self.oauth_error = None
    try:
        body: Any = json.loads(response)
    except (json.JSONDecodeError, TypeError):
        body = None

    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            self.reference_id = err.get("referenceId")
            self.code = err.get("code")
            self.message = err.get("message")
        elif isinstance(err, str):
            self.oauth_error = err
            self.code = body.get("error_code")
            self.message = body.get("error_description") or err

    Exception.__init__(self, self.message or response)


def patch_psnawp() -> None:
    """Install the tolerant error parser on the PSNAWP base exception."""
    psnawp_exceptions.PSNAWPError.__init__ = _psnawp_error_init


def is_auth_error(error: Exception) -> bool:
    """Return True if the error means the credentials must be renewed."""
    if isinstance(error, PSNAWPAuthenticationError):
        return True
    return (
        isinstance(error, PSNAWPBadRequestError)
        and getattr(error, "oauth_error", None) in OAUTH_AUTH_ERRORS
    )
