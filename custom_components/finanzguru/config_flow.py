from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FinanzguruApi, FinanzguruAuthError, FinanzguruError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_EMAIL,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES_AT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class FinanzguruConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            email: str = user_input[CONF_EMAIL].strip()
            refresh_token: str = user_input[CONF_REFRESH_TOKEN].strip()
            access_token: str | None = user_input.get(CONF_ACCESS_TOKEN)
            if access_token is not None:
                access_token = access_token.strip() or None

            session = async_get_clientsession(self.hass)
            api = FinanzguruApi(
                session,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
            try:
                tokens = await api.async_refresh_access_token()
                await api.async_get_bank_accounts()
            except FinanzguruAuthError:
                errors["base"] = "invalid_auth"
            except FinanzguruError as err:
                _LOGGER.error("Finanzguru login failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during Finanzguru login")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(email.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=email,
                    data={
                        CONF_EMAIL: email,
                        CONF_ACCESS_TOKEN: tokens.access_token,
                        CONF_REFRESH_TOKEN: tokens.refresh_token,
                        CONF_TOKEN_EXPIRES_AT: tokens.expires_at.timestamp(),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_REFRESH_TOKEN): str,
                vol.Optional(CONF_ACCESS_TOKEN): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, user_input: dict):
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict | None = None):
        errors: dict[str, str] = {}

        if user_input is not None and getattr(self, "_reauth_entry", None):
            email: str = user_input[CONF_EMAIL].strip()
            refresh_token: str = user_input[CONF_REFRESH_TOKEN].strip()
            access_token: str | None = user_input.get(CONF_ACCESS_TOKEN)
            if access_token is not None:
                access_token = access_token.strip() or None

            session = async_get_clientsession(self.hass)
            api = FinanzguruApi(
                session,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
            try:
                tokens = await api.async_refresh_access_token()
                await api.async_get_bank_accounts()
            except FinanzguruAuthError:
                errors["base"] = "invalid_auth"
            except FinanzguruError as err:
                _LOGGER.error("Finanzguru reauth failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during Finanzguru reauth")
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={
                        **self._reauth_entry.data,
                        CONF_EMAIL: email,
                        CONF_ACCESS_TOKEN: tokens.access_token,
                        CONF_REFRESH_TOKEN: tokens.refresh_token,
                        CONF_TOKEN_EXPIRES_AT: tokens.expires_at.timestamp(),
                    },
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_REFRESH_TOKEN): str,
                vol.Optional(CONF_ACCESS_TOKEN): str,
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            errors=errors,
        )
