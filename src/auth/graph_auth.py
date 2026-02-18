"""
Microsoft Graph API Authentication
RS&Co. Enterprise Integration Layer

Uses OAuth 2.0 Client Credentials flow (app-only) via MSAL.
Requires an Entra ID App Registration with the following API permissions:
  - Sites.ReadWrite.All       (SharePoint)
  - Tasks.ReadWrite           (Microsoft To Do / Planner)
  - Dynamics 365 permissions are handled via D365 Web API directly
"""

import os
import logging
from functools import lru_cache

import msal

logger = logging.getLogger(__name__)


class GraphAuthConfig:
    """Reads auth config from environment variables."""

    TENANT_ID: str = os.environ["AZURE_TENANT_ID"]
    CLIENT_ID: str = os.environ["AZURE_CLIENT_ID"]
    CLIENT_SECRET: str = os.environ["AZURE_CLIENT_SECRET"]

    # Scopes for app-only auth (client credentials)
    GRAPH_SCOPES: list[str] = ["https://graph.microsoft.com/.default"]
    D365_SCOPES: list[str] = [f"{os.environ.get('D365_RESOURCE_URL', '')}/.default"]


class GraphTokenProvider:
    """
    Acquires and caches access tokens for Microsoft Graph and Dynamics 365.
    Uses MSAL ConfidentialClientApplication with in-memory token cache.
    """

    def __init__(self, config: GraphAuthConfig | None = None):
        self._config = config or GraphAuthConfig()
        self._graph_app = msal.ConfidentialClientApplication(
            client_id=self._config.CLIENT_ID,
            client_credential=self._config.CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{self._config.TENANT_ID}",
        )

    def get_graph_token(self) -> str:
        """Returns a valid Bearer token for Microsoft Graph API."""
        return self._acquire_token(
            self._graph_app, self._config.GRAPH_SCOPES, audience="Graph"
        )

    def get_d365_token(self) -> str:
        """Returns a valid Bearer token for Dynamics 365 Web API."""
        return self._acquire_token(
            self._graph_app, self._config.D365_SCOPES, audience="Dynamics 365"
        )

    def _acquire_token(
        self, app: msal.ConfidentialClientApplication, scopes: list[str], audience: str
    ) -> str:
        result = app.acquire_token_silent(scopes, account=None)
        if not result:
            logger.debug("Cache miss — acquiring new token for %s", audience)
            result = app.acquire_token_for_client(scopes=scopes)

        if "access_token" not in result:
            error = result.get("error_description", result.get("error", "unknown"))
            raise RuntimeError(f"Failed to acquire {audience} token: {error}")

        logger.debug("Token acquired for %s (expires_in=%s)", audience, result.get("expires_in"))
        return result["access_token"]


# Module-level singleton — import and use directly.
@lru_cache(maxsize=1)
def get_token_provider() -> GraphTokenProvider:
    return GraphTokenProvider()
