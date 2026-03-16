from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

import requests


class AxonFiProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        relayer_url = credentials.get("relayer_url", "https://relay.axonfi.xyz").rstrip(
            "/"
        )
        try:
            resp = requests.get(f"{relayer_url}/health", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "ok":
                raise ToolProviderCredentialValidationError(
                    "Relayer health check failed"
                )
        except requests.RequestException as e:
            raise ToolProviderCredentialValidationError(
                f"Cannot connect to AxonFi relayer at {relayer_url}: {e}"
            )

        if not credentials.get("bot_private_key", "").startswith("0x"):
            raise ToolProviderCredentialValidationError(
                "Bot private key must start with 0x"
            )

        if not credentials.get("vault_address", "").startswith("0x"):
            raise ToolProviderCredentialValidationError(
                "Vault address must start with 0x"
            )
