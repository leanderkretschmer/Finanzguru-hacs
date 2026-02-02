from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    currency = hass.config.currency or "EUR"

    async_add_entities(
        [
            FinanzguruMonthlyExpensesSensor(coordinator, entry, currency),
            FinanzguruMonthlyIncomeSensor(coordinator, entry, currency),
            FinanzguruTodaySpendingSensor(coordinator, entry, currency),
            FinanzguruContractsOverviewSensor(coordinator, entry, currency),
            FinanzguruBudgetUsageSensor(coordinator, entry),
        ],
        update_before_add=False,
    )


class FinanzguruBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data is not None


class FinanzguruMonthlyExpensesSensor(FinanzguruBaseSensor):
    _attr_name = "Monatliche Ausgaben"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator, entry: ConfigEntry, currency: str) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_monthly_expenses"
        self._attr_native_unit_of_measurement = currency

    @property
    def native_value(self) -> float | None:
        monthly = (self.coordinator.data or {}).get("monthly") or {}
        value = monthly.get("expenses")
        return float(value) if isinstance(value, (int, float)) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        monthly = (self.coordinator.data or {}).get("monthly") or {}
        categories = monthly.get("categories")
        return {"kategorien": categories} if categories is not None else {}


class FinanzguruMonthlyIncomeSensor(FinanzguruBaseSensor):
    _attr_name = "Monatliche Einnahmen"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator, entry: ConfigEntry, currency: str) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_monthly_income"
        self._attr_native_unit_of_measurement = currency

    @property
    def native_value(self) -> float | None:
        monthly = (self.coordinator.data or {}).get("monthly") or {}
        value = monthly.get("income")
        return float(value) if isinstance(value, (int, float)) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        monthly = (self.coordinator.data or {}).get("monthly") or {}
        categories = monthly.get("categories")
        return {"kategorien": categories} if categories is not None else {}


class FinanzguruTodaySpendingSensor(FinanzguruBaseSensor):
    _attr_name = "Heutige Ausgaben"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator, entry: ConfigEntry, currency: str) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_today_spending"
        self._attr_native_unit_of_measurement = currency

    @property
    def native_value(self) -> float | None:
        value = (self.coordinator.data or {}).get("today_spending")
        return float(value) if isinstance(value, (int, float)) else None


class FinanzguruContractsOverviewSensor(FinanzguruBaseSensor):
    _attr_name = "Verträge"

    def __init__(self, coordinator, entry: ConfigEntry, currency: str) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_contracts_overview"
        self._currency = currency

    @property
    def native_value(self) -> int:
        contracts = (self.coordinator.data or {}).get("contracts") or []
        return len(contracts) if isinstance(contracts, list) else 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        contracts = (self.coordinator.data or {}).get("contracts") or []
        normalized: list[dict[str, Any]] = []
        if isinstance(contracts, list):
            for item in contracts:
                if not isinstance(item, dict):
                    continue
                normalized.append(
                    {
                        "name": item.get("name") or item.get("title"),
                        "price": item.get("price") or item.get("amount"),
                        "payment_rate": item.get("payment_rate") or item.get("rate"),
                        "currency": item.get("currency") or self._currency,
                    }
                )
        return {"list": normalized}


class FinanzguruBudgetUsageSensor(FinanzguruBaseSensor):
    _attr_name = "Budget-Auslastung"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_budget_usage"

    @property
    def native_value(self) -> float | None:
        budget = (self.coordinator.data or {}).get("budgets") or {}
        if not isinstance(budget, dict):
            return None

        value = budget.get("used_percent")
        if value is None:
            value = budget.get("usage")
        if isinstance(value, (int, float)):
            return float(value)

        spent = budget.get("spent")
        limit_ = budget.get("limit")
        if isinstance(spent, (int, float)) and isinstance(limit_, (int, float)) and limit_:
            return float(spent) / float(limit_) * 100.0

        return None
