"""SGSmart Entity class."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import BlueprintDataUpdateCoordinator


class IntegrationBlueprintEntity(CoordinatorEntity[BlueprintDataUpdateCoordinator]):
    """SGSmart Entity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: BlueprintDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
            name="SG Smart Hub",
            manufacturer="SG Smart",
            model="SG Smart Integration",
        )


class SGSmartDeviceEntity(CoordinatorEntity[BlueprintDataUpdateCoordinator]):
    """SGSmart Device Entity class for individual devices."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: BlueprintDataUpdateCoordinator,
        device_uuid: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize device entity."""
        super().__init__(coordinator)
        self._device_uuid = device_uuid
        self._device_data = device_data
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{device_uuid}"

        # Create device info for this specific device
        device_name = device_data.get("name", f"SG Smart Device {device_uuid}")
        mesh_id = device_data.get("mesh_id")
        device_model = f"Type {device_data.get('type', 'Unknown')}"
        firmware_version = device_data.get("firmware_version")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_uuid)},
            name=device_name,
            manufacturer="SG Smart",
            model=device_model,
            serial_number=mesh_id,
            sw_version=firmware_version,
        )

    @property
    def device_data(self) -> dict[str, Any] | None:
        """Get current device data from coordinator."""
        if not self.coordinator.data:
            return None

        # Find this device in the coordinator data
        devices = self.coordinator.data.get("devices", [])
        if isinstance(devices, list):
            for device in devices:
                if isinstance(device, dict) and device.get("uuid") == self._device_uuid:
                    return device

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.device_data is not None
