"""SG Smart API Client."""

from __future__ import annotations

import json
import socket
from typing import Any

import aiohttp
import async_timeout

from .const import BASE_URL, LOGIN_ENDPOINT, DEVICE_ENDPOINT, ROUTE_URL


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

    async def _api_call_without_auth(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Make an API call without authentication."""
        return await self._api_wrapper(
            method=method,
            url=url,
            data=data,
            headers=headers,
        )

    async def async_get_devices(self) -> Any:
        """Get data from the SG Smart API."""
        return await self._api_call_with_auth(
            method="get", url=f"{self._base_url}{DEVICE_ENDPOINT}"
        )

    async def async_get_control_urls(self, sector_uuid: str) -> Any:
        """Get control URLs for devices in a specific sector."""
        return await self._api_call_without_auth(
            method="post",
            url=ROUTE_URL,
            data={"sector_uuid": sector_uuid},
            headers={"Content-Type": "application/json"},
        )

    async def async_control_device_websocket(
        self,
        control_url_data: dict[str, Any],
        sector_uuid: str,
        mesh_id: int,
        command_data: str,
    ) -> None:
        """Send control command to device via WebSocket."""
        if (
            not control_url_data
            or "host" not in control_url_data
            or "path" not in control_url_data
        ):
            msg = "Invalid control URL data"
            raise SGSmartApiClientError(msg)

        # Construct WebSocket URL
        ws_url = f"{control_url_data['host']}{control_url_data['path']}/socket.io/?EIO=3&transport=websocket"
        # Convert http/https to ws/wss
        ws_url = ws_url.replace("https://", "wss://").replace("http://", "ws://")

        # Prepare WebSocket message
        message = [
            "extModelMessage",
            f"s_{sector_uuid.lower()}",
            mesh_id,
            65283,
            command_data,
        ]
        # Prepend 42 to indicate message type
        message_json = json.dumps(message)
        message_with_type = f"42{message_json}"
        try:
            #             # Use proxy and ignore SSL certificate verification
            # connector = aiohttp.TCPConnector(
            #     verify_ssl=False,
            #     force_close=True,
            # )
            # proxy_url = "http://host.docker.internal:8080"

            # # Create a new session with the custom connector for WebSocket
            # async with (
            #     aiohttp.ClientSession(connector=connector) as ws_session,
            #     ws_session.ws_connect(
            #         ws_url,
            #         proxy=proxy_url,
            #         ssl=False,
            #     ) as ws,
            # ):

            async with self._session.ws_connect(ws_url) as ws:
                await ws.send_str(message_with_type)
                # Wait for response
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        # Process response if needed
                        break
                    if msg.type == aiohttp.WSMsgType.ERROR:
                        msg_error = f"WebSocket error: {ws.exception()}"
                        raise SGSmartApiClientCommunicationError(msg_error)
        except Exception as exception:
            msg = f"WebSocket communication error: {exception}"
            raise SGSmartApiClientCommunicationError(msg) from exception

    async def async_turn_on_light(
        self,
        control_url_data: dict[str, Any],
        sector_uuid: str,
        mesh_id: int,
    ) -> None:
        """Turn on a light."""
        # Using the provided example command for turning on
        command_data = "23BC0100010000"

        await self.async_control_device_websocket(
            control_url_data=control_url_data,
            sector_uuid=sector_uuid,
            mesh_id=mesh_id,
            command_data=command_data,
        )

    async def async_turn_off_light(
        self,
        control_url_data: dict[str, Any],
        sector_uuid: str,
        mesh_id: int,
    ) -> None:
        """Turn off a light."""
        # Turn-off command (may need adjustment based on actual protocol)
        command_data = "23BC0000010000"

        await self.async_control_device_websocket(
            control_url_data=control_url_data,
            sector_uuid=sector_uuid,
            mesh_id=mesh_id,
            command_data=command_data,
        )

    async def async_dim_light(
        self,
        control_url_data: dict[str, Any],
        sector_uuid: str,
        mesh_id: int,
        brightness_percent: int,
    ) -> None:
        """Dim a light to a specific brightness percentage (1-100)."""
        if not 1 <= brightness_percent <= 100:
            msg = f"Brightness must be between 1 and 100, got {brightness_percent}"
            raise SGSmartApiClientError(msg)

        # Convert percentage to hex
        brightness_hex = f"{brightness_percent:02X}"

        # No idea what the suffix means, might be something with sequence. For now always use 01
        suffix = "01"

        # Construct command: 23BC01[brightness_hex][suffix]0000
        command_data = f"23BC01{brightness_hex}{suffix}0000"

        await self.async_control_device_websocket(
            control_url_data=control_url_data,
            sector_uuid=sector_uuid,
            mesh_id=mesh_id,
            command_data=command_data,
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
