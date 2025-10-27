"""DataUpdateCoordinator for custom_components/sgsmart."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SGSmartApiClientAuthenticationError,
    SGSmartApiClientError,
)

if TYPE_CHECKING:
    from .data import IntegrationBlueprintConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class BlueprintDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: IntegrationBlueprintConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            # First get the device data
            device_data = (
                await self.config_entry.runtime_data.client.async_get_devices()
            )

            # Extract sectors and get control URLs for the first sector
            if device_data and "sectors" in device_data:
                sectors = device_data["sectors"]
                if isinstance(sectors, list) and len(sectors) > 0:
                    first_sector_uuid = sectors[0].get("uuid")
                    if first_sector_uuid:
                        # Get control URLs for the first sector
                        client = self.config_entry.runtime_data.client
                        control_data = await client.async_get_control_urls(
                            first_sector_uuid
                        )
                        # Merge control data with device data if needed
                        if control_data:
                            device_data["control_urls"] = control_data

        except SGSmartApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except SGSmartApiClientError as exception:
            raise UpdateFailed(exception) from exception
        else:
            return device_data
