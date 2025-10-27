"""Light platform for SG Smart dimmer devices."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.components.light.const import ColorMode

from .entity import SGSmartDeviceEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import BlueprintDataUpdateCoordinator
    from .data import IntegrationBlueprintConfigEntry

# Constants for SG Smart dimmer devices
DEVICE_TYPE_DIMMER = 1  # Type 1 devices are dimmers based on JSON data

# Light description for dimmer devices
DIMMER_LIGHT_DESCRIPTION = LightEntityDescription(
    key="dimmer",
    name="Dimmer",
    icon="mdi:brightness-6",
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: IntegrationBlueprintConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform for SG Smart dimmer devices."""
    coordinator = entry.runtime_data.coordinator

    # Add dimmer light entities for type 1 devices
    device_entities = []
    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data["devices"]
        if isinstance(devices, list):
            for device in devices:
                if isinstance(device, dict) and "uuid" in device:
                    device_uuid = device["uuid"]
                    device_type = device.get("type")

                    # Only create light entities for type 1 (dimmer) devices
                    if device_type == DEVICE_TYPE_DIMMER:
                        device_entities.append(
                            SGSmartDimmerLight(
                                coordinator=coordinator,
                                device_uuid=device_uuid,
                                device_data=device,
                                entity_description=DIMMER_LIGHT_DESCRIPTION,
                            )
                        )

    async_add_entities(device_entities)


class SGSmartDimmerLight(SGSmartDeviceEntity, LightEntity):
    """SG Smart Dimmer Light class."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes: ClassVar[set[ColorMode]] = {ColorMode.BRIGHTNESS}

    def __init__(
        self,
        coordinator: BlueprintDataUpdateCoordinator,
        device_uuid: str,
        device_data: dict[str, Any],
        entity_description: LightEntityDescription,
    ) -> None:
        """Initialize the dimmer light class."""
        super().__init__(coordinator, device_uuid, device_data)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{device_uuid}_{entity_description.key}"
        device_name = device_data.get("name", f"Dimmer {device_uuid}")
        self._attr_name = f"{device_name}"

    @property
    def is_on(self) -> bool:
        """Return true if dimmer is on."""
        device_data = self.device_data
        if not device_data:
            return False

        # Check status field (0 = off, 1+ = on in SG Smart)
        status = device_data.get("status")
        if status is not None:
            return status > 0

        return False

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        device_data = self.device_data
        if not device_data:
            return None

        # Get brightness level from device data
        # In SG Smart, level ranges from min_level to max_level
        min_level = device_data.get("min_level", 10)
        max_level = device_data.get("max_level", 100)

        # For now, we don't have current level in the device data from the API
        # We'll need to get this from the actual device state when available
        # For now, if device is on, return calculated brightness
        if self.is_on:
            start_up_level = device_data.get("start_up_level", 30)
            # Convert from device range to Home Assistant range (0-255)
            if max_level > min_level:
                brightness_percent = (start_up_level - min_level) / (
                    max_level - min_level
                )
                return int(brightness_percent * 255)
            return 128  # Default middle brightness

        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the dimmer."""
        # Device control API calls would be implemented here
        # when the SG Smart API supports device control
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None:
            # Convert brightness from 0-255 to device min_level-max_level range
            device_data = self.device_data
            if device_data:
                min_level = device_data.get("min_level", 10)
                max_level = device_data.get("max_level", 100)
                # Calculate device level for future API implementation
                _device_level = min_level + (brightness / 255) * (max_level - min_level)
                # Future: Send device control command with _device_level

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the dimmer."""
        # Device control API calls would be implemented here
        # when the SG Smart API supports device control
        await self.coordinator.async_request_refresh()
