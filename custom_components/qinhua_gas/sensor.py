"""Sensor platform for 西安天然气 integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Callable, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    ATTR_BALANCE,
    ATTR_DATA,
    ATTR_PRICE,
    ATTR_USAGE_DAYS,
    DOMAIN,
    NAME,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up 西安天然气 sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        XianGasBalanceSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class XianGasBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for 西安天然气 sensors."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        name: str,
        icon: str,
        unit: str,
        device_class: Optional[str] = None,
        state_class: Optional[str] = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._attr_name = f"{NAME} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=NAME
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.data:
            return False
        return super().available


class XianGasBalanceSensor(XianGasBaseSensor):
    """Sensor for gas balance."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            config_entry,
            "xian_gas",
            "天然气",
            "mdi:gas-cylinder",
            "¥",
            SensorDeviceClass.MONETARY,
            SensorStateClass.TOTAL,
        )
        self.entity_id = "sensor.xian_gas"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data or not self.coordinator.data.get("ranqi"):
            return None
        return self.coordinator.data.get("ranqi", {}).get(ATTR_BALANCE)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data or not self.coordinator.data.get("ranqi"):
            return {}
        ranqi_data = self.coordinator.data.get("ranqi", {})
        return {
            "日均消费": ranqi_data.get(ATTR_PRICE),
            "剩余天数": ranqi_data.get(ATTR_USAGE_DAYS),
            "充值明细": self.coordinator.data.get("ranqidata", []),
        }