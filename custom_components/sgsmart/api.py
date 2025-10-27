"""SG Smart API Client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout

from .const import BASE_URL, LOGIN_ENDPOINT


class SGSmartApiClientError(Exception):
    """Exception to indicate a general API error."""


class SGSmartApiClientCommunicationError(
    SGSmartApiClientError,
):
    """Exception to indicate a communication error."""


class SGSmartApiClientAuthenticationError(
    SGSmartApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials or session expired"
        raise SGSmartApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class SGSmartApiClient:
    """SG Smart API Client."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize SG Smart API Client."""
        self._username = username
        self._password = password
        self._session = session
        self._base_url = BASE_URL
        self._is_authenticated = False

    async def async_login(self) -> dict[str, Any]:
        """Login to SG Smart service using cookie-based authentication."""
        login_data = {
            "email": self._username,
            "password": self._password,
            "platform": "flutter_android",
            "app_bundle_id": "com.sgas.leddimapp",
            "app_version": "4.34.785",
            "lang": "en",
        }

        response = await self._api_wrapper(
            method="post",
            url=f"{self._base_url}{LOGIN_ENDPOINT}",
            data=login_data,
            headers={"Content-Type": "application/json"},
        )

        # Mark as authenticated - cookies will be stored in the session automatically
        self._is_authenticated = True

        return response

    async def _ensure_authenticated(self) -> None:
        """Ensure the client is authenticated, login if necessary."""
        if not self._is_authenticated:
            await self.async_login()

    async def _api_call_with_auth(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Make an API call with automatic re-authentication on auth failure."""
        await self._ensure_authenticated()

        try:
            return await self._api_wrapper(
                method=method,
                url=url,
                data=data,
                headers=headers,
            )
        except SGSmartApiClientAuthenticationError:
            # Authentication failed, try to re-login once
            self._is_authenticated = False
            await self.async_login()
            return await self._api_wrapper(
                method=method,
                url=url,
                data=data,
                headers=headers,
            )

    async def async_get_data(self) -> Any:
        """Get data from the SG Smart API."""

        return await self._api_call_with_auth(
            method="get", url=f"{self._base_url}/sg/api/download"
        )

    async def async_logout(self) -> None:
        """Logout from SG Smart service by clearing cookies."""
        # Clear cookies from the session
        self._session.cookie_jar.clear()
        self._is_authenticated = False

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise SGSmartApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise SGSmartApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise SGSmartApiClientError(
                msg,
            ) from exception
