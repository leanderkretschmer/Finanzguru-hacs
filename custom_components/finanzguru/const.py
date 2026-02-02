from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Final

DOMAIN = "finanzguru"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_TOKEN_EXPIRES_AT = "token_expires_at"

UPDATE_INTERVAL = timedelta(minutes=30)

_MANIFEST_PATH = Path(__file__).parent / "manifest.json"
INTEGRATION_VERSION: Final[str] = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8")).get(
    "version",
    "0.0.0",
)

URL_BASE: Final[str] = "/finanzguru"
JSMODULES: Final[list[dict[str, str]]] = [
    {"name": "Finanzguru Cards", "filename": "finanzguru-cards.js", "version": INTEGRATION_VERSION}
]
