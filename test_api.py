"""Test script for SG Smart API client.

This script demonstrates how to use the SGSmartApiClient with cookie-based authentication.
Requires SGSMART_USERNAME and SGSMART_PASSWORD environment variables.

Usage:
    export SGSMART_USERNAME=your_username
    export SGSMART_PASSWORD=your_password
    python test_api.py
"""

import asyncio
import os
import sys

import aiohttp

from custom_components.sgsmart.api import (
    SGSmartApiClient,
    SGSmartApiClientAuthenticationError,
    SGSmartApiClientCommunicationError,
    SGSmartApiClientError,
)


def get_credentials() -> tuple[str, str]:
    """Get username and password from environment variables."""
    username = os.getenv("SGSMART_USERNAME")
    password = os.getenv("SGSMART_PASSWORD")

    if not username or not password:
        print(
            "Error: Environment variables SGSMART_USERNAME and "
            "SGSMART_PASSWORD are required."
        )
        print("Example: export SGSMART_USERNAME=your_username")
        print("         export SGSMART_PASSWORD=your_password")
        sys.exit(1)

    return username, password


async def test_api_client() -> None:
    """Test the SG Smart API client with cookie-based authentication."""
    # Get credentials from command line input
    username, password = get_credentials()

    async with aiohttp.ClientSession() as session:
        client = SGSmartApiClient(
            username=username,
            password=password,
            session=session,
        )

        try:
            # Test login - cookies will be stored automatically
            print("Testing login...")
            login_response = await client.async_login()
            print(f"Login response: {login_response}")

            # Test getting data - uses cookies for authentication
            print("Testing data retrieval...")
            data = await client.async_get_data()
            print(f"Data: {data}")

        except SGSmartApiClientAuthenticationError as e:
            print(f"Authentication error: {e}")
        except SGSmartApiClientCommunicationError as e:
            print(f"Communication error: {e}")
        except SGSmartApiClientError as e:
            print(f"General API error: {e}")


if __name__ == "__main__":
    asyncio.run(test_api_client())
