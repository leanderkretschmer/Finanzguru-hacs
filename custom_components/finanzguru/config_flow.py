from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FinanzguruApi, FinanzguruAuthError, FinanzguruError
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)


class FinanzguruConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            email: str = user_input[CONF_EMAIL].strip()
            password: str = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            api = FinanzguruApi(session)
            try:
                tokens = await api.async_login_with_password(email, password)
                if not tokens.refresh_token:
                    raise FinanzguruAuthError("Missing refresh token")
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
                        "access_token": tokens.access_token,
                        "refresh_token": tokens.refresh_token,
                        "token_expires_at": tokens.expires_at.timestamp(),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
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
            password: str = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            api = FinanzguruApi(session)
            try:
                tokens = await api.async_login_with_password(email, password)
                if not tokens.refresh_token:
                    raise FinanzguruAuthError("Missing refresh token")
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
                        "access_token": tokens.access_token,
                        "refresh_token": tokens.refresh_token,
                        "token_expires_at": tokens.expires_at.timestamp(),
                    },
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            errors=errors,
        )
