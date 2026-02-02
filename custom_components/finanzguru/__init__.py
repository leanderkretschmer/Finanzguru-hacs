from __future__ import annotations

from datetime import datetime, timezone
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FinanzguruApi, FinanzguruAuthError, FinanzguruError, FinanzguruTokens
from .const import DOMAIN, UPDATE_INTERVAL
from .frontend import async_register_frontend

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


def _tokens_from_entry(entry: ConfigEntry) -> tuple[str | None, str | None, datetime | None]:
    access_token = entry.data.get("access_token")
    refresh_token = entry.data.get("refresh_token")
    token_expires_at = entry.data.get("token_expires_at")

    if not isinstance(access_token, str) or not isinstance(refresh_token, str):
        return None, None, None

    expires_at: datetime | None = None
    if isinstance(token_expires_at, (int, float)):
        expires_at = datetime.fromtimestamp(float(token_expires_at), tz=timezone.utc)

    return access_token, refresh_token, expires_at


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    session = async_get_clientsession(hass)
    await async_register_frontend(hass)

    async def _async_update_tokens(tokens: FinanzguruTokens) -> None:
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_expires_at": tokens.expires_at.timestamp(),
            },
        )

    access_token, refresh_token, expires_at = _tokens_from_entry(entry)
    api = FinanzguruApi(
        session,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        token_updater=_async_update_tokens,
    )

    async def _async_update_data() -> dict:
        try:
            overview = await api.async_get_overview()
            accounts = overview.get("accounts") or {}
            budgets = overview.get("budgets") or {}
            contracts = overview.get("contracts") or {}

            return {
                "monthly": api.extract_monthly_expenses_income(accounts),
                "today_spending": api.extract_today_spending(accounts),
                "contracts": api.extract_contracts(contracts),
                "budgets": api.extract_budget_status(budgets),
            }
        except FinanzguruAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except FinanzguruError as err:
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Finanzguru",
        update_interval=UPDATE_INTERVAL,
        update_method=_async_update_data,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
