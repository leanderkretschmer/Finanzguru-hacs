from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

import aiohttp


class FinanzguruError(Exception):
    pass


class FinanzguruAuthError(FinanzguruError):
    pass


@dataclass(frozen=True)
class FinanzguruTokens:
    access_token: str
    refresh_token: str
    expires_at: datetime


TokenUpdater = Callable[[FinanzguruTokens], Awaitable[None]]


class FinanzguruApi:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
        token_updater: TokenUpdater | None = None,
        base_url: str = "https://api.finanzguru.de",
        request_timeout: aiohttp.ClientTimeout | None = None,
    ) -> None:
        self._session = session
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._expires_at = expires_at
        self._token_updater = token_updater
        self._base_url = base_url.rstrip("/")
        self._timeout = request_timeout or aiohttp.ClientTimeout(total=30)
        self._token_lock = asyncio.Lock()

    @property
    def has_tokens(self) -> bool:
        return bool(self._access_token and self._refresh_token and self._expires_at)

    async def async_login_with_password(self, email: str, password: str) -> FinanzguruTokens:
        payload = {
            "grant_type": "password",
            "username": email,
            "password": password,
        }
        data = await self._async_request("POST", "/oauth/token", json=payload, auth=False)
        tokens = self._tokens_from_response(data)
        await self._async_apply_tokens(tokens)
        return tokens

    async def async_refresh_access_token(self) -> FinanzguruTokens:
        if not self._refresh_token:
            raise FinanzguruAuthError("Missing refresh token")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }
        data = await self._async_request("POST", "/oauth/token", json=payload, auth=False)
        tokens = self._tokens_from_response(data)
        if not tokens.refresh_token:
            tokens = FinanzguruTokens(
                access_token=tokens.access_token,
                refresh_token=self._refresh_token,
                expires_at=tokens.expires_at,
            )
        await self._async_apply_tokens(tokens)
        return tokens

    async def async_ensure_valid_token(self) -> None:
        # Token-Handling: Vor jedem API-Call wird geprüft, ob der Access-Token bald abläuft.
        # Falls ja, wird automatisch mit dem Refresh-Token ein neuer Access-Token angefordert
        # und per token_updater in der ConfigEntry-Data persistiert. So bleibt die Anmeldung
        # langfristig gültig, ohne dass der Nutzer sich regelmäßig neu anmelden muss.
        if not self.has_tokens:
            raise FinanzguruAuthError("Not authenticated")

        now = datetime.now(timezone.utc)
        if self._expires_at and now + timedelta(seconds=60) < self._expires_at:
            return

        async with self._token_lock:
            now = datetime.now(timezone.utc)
            if self._expires_at and now + timedelta(seconds=60) < self._expires_at:
                return
            await self.async_refresh_access_token()

    async def async_get_bank_accounts(self) -> dict[str, Any]:
        return await self._async_request("GET", "/bank/accounts")

    async def async_get_budgets(self) -> dict[str, Any]:
        return await self._async_request("GET", "/analysis/budgets")

    async def async_get_contracts(self) -> dict[str, Any]:
        return await self._async_request("GET", "/contracts")

    async def async_get_overview(self) -> dict[str, Any]:
        accounts, budgets, contracts = await asyncio.gather(
            self.async_get_bank_accounts(),
            self.async_get_budgets(),
            self.async_get_contracts(),
        )
        return {
            "accounts": accounts,
            "budgets": budgets,
            "contracts": contracts,
        }

    def extract_monthly_expenses_income(self, accounts_payload: dict[str, Any]) -> dict[str, Any]:
        monthly = (
            accounts_payload.get("monthly")
            or accounts_payload.get("analysis", {}).get("monthly")
            or {}
        )
        expenses = monthly.get("expenses")
        income = monthly.get("income")
        categories = monthly.get("categories") or monthly.get("by_category") or {}
        return {"expenses": expenses, "income": income, "categories": categories}

    def extract_today_spending(self, accounts_payload: dict[str, Any]) -> float | None:
        today = accounts_payload.get("today_spending")
        if today is None:
            today = accounts_payload.get("today", {}).get("spending")
        return today

    def extract_contracts(self, contracts_payload: dict[str, Any]) -> list[dict[str, Any]]:
        contracts = contracts_payload.get("contracts")
        if isinstance(contracts, list):
            return contracts
        items = contracts_payload.get("items")
        if isinstance(items, list):
            return items
        return []

    def extract_budget_status(self, budgets_payload: dict[str, Any]) -> dict[str, Any]:
        current = budgets_payload.get("current") or budgets_payload.get("budget") or {}
        return current if isinstance(current, dict) else {}

    async def _async_apply_tokens(self, tokens: FinanzguruTokens) -> None:
        self._access_token = tokens.access_token
        self._refresh_token = tokens.refresh_token
        self._expires_at = tokens.expires_at
        if self._token_updater:
            await self._token_updater(tokens)

    def _tokens_from_response(self, data: dict[str, Any]) -> FinanzguruTokens:
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in")

        if not access_token or not isinstance(expires_in, (int, float)):
            raise FinanzguruAuthError("Token response incomplete")

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=float(expires_in))
        return FinanzguruTokens(
            access_token=str(access_token),
            refresh_token=str(refresh_token or ""),
            expires_at=expires_at,
        )

    async def _async_request(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"

        headers = kwargs.pop("headers", {})
        if auth:
            await self.async_ensure_valid_token()
            headers = {**headers, "Authorization": f"Bearer {self._access_token}"}

        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                timeout=self._timeout,
                **kwargs,
            ) as resp:
                if resp.status in (401, 403):
                    raise FinanzguruAuthError(f"Auth failed ({resp.status})")
                resp.raise_for_status()
                data = await resp.json(content_type=None)
                if isinstance(data, dict):
                    return data
                return {"data": data}
        except FinanzguruAuthError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise FinanzguruError(str(err)) from err
