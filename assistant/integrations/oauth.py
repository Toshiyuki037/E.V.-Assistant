"""
E.V.I.E. - OAuth Integration Interface

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Defines the provider-independent OAuth lifecycle used by Phase 9.

Real provider OAuth implementations will conform to this interface.
"""

from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)


# ---------------------------------------------------------------------------
# OAuth Provider
# ---------------------------------------------------------------------------

class OAuthProvider(
    ABC
):
    """
    Provider-independent OAuth interface.
    """

    provider_name: str = ""


    @abstractmethod
    def get_authorization_url(
        self,
        scopes: list[str],
        state: str,
    ) -> str:
        raise NotImplementedError


    @abstractmethod
    def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict:
        raise NotImplementedError


    @abstractmethod
    def refresh_credentials(
        self,
        credentials: dict,
    ) -> dict:
        raise NotImplementedError


    @abstractmethod
    def revoke_credentials(
        self,
        credentials: dict,
    ) -> bool:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# OAuth Result Validation
# ---------------------------------------------------------------------------

def validate_oauth_credentials(
    credentials: dict,
):
    """
    Performs basic structural validation without exposing secrets.
    """

    if not isinstance(
        credentials,
        dict,
    ):

        return False


    access_token = (
        credentials.get(
            "access_token"
        )
    )


    return bool(
        access_token
    )