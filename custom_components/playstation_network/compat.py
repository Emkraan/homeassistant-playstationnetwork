"""Compatibility fixes for the PSNAWP library."""

import functools
import json
import threading
import time
from collections.abc import Callable
from typing import Any, Final

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


# Refresh this many seconds before the real expiry, so a request can never
# start with a token that expires in flight and come back as 401.
REFRESH_MARGIN_SECONDS: Final = 60


def install_refresh_guard(
    authenticator: Any,
    on_rotation: Callable[[], None] | None = None,
) -> None:
    """Serialize token refresh on one PSNAWP client and report rotations.

    PSNAWP refreshes the access token inline, on whichever worker thread
    notices the expiry. This integration runs every coordinator and notify
    call on its own executor thread against one shared client, so when the
    token expires several threads can start a refresh at once. Sony rotates
    the refresh token on every renewal and rejects a replayed one with
    ``invalid_grant``, which the integration can only read as a failed
    login - the reauth prompt of issue #39.

    Hold a per-client lock around the library's refresh (it re-checks the
    expiry after acquisition, so only the first thread posts), force the
    refresh ``REFRESH_MARGIN_SECONDS`` ahead of the real expiry, and call
    ``on_rotation`` after a rotation so the caller can persist the new pair
    immediately instead of after the next poll.
    """
    lock = threading.Lock()
    original = authenticator.fetch_access_token_from_refresh

    @functools.wraps(original)
    def guarded_refresh() -> None:
        with lock:
            token_response = authenticator.token_response
            if token_response is not None:
                expires_at = token_response.get("access_token_expires_at")
                if expires_at is not None and expires_at - REFRESH_MARGIN_SECONDS > time.time():
                    return
                # Pull the expiry into the past so the library refreshes now
                # instead of returning early on a token that expires inside
                # the margin. If the refresh then fails, the earlier expiry
                # only means the next request retries it sooner.
                token_response["access_token_expires_at"] = time.time()
            before = token_response
            original()
            rotated = authenticator.token_response is not before
        if rotated and on_rotation is not None:
            on_rotation()

    authenticator.fetch_access_token_from_refresh = guarded_refresh
