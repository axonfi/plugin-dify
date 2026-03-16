from collections.abc import Generator
from typing import Any

import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class GetBalanceTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        relayer_url = self.runtime.credentials["relayer_url"].rstrip("/")
        vault_address = self.runtime.credentials["vault_address"]
        chain_id = self.runtime.credentials["chain_id"]

        try:
            resp = requests.get(
                f"{relayer_url}/v1/vaults/{vault_address}/balance",
                params={"chainId": chain_id},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            yield self.create_text_message(f"Failed to fetch balance: {e}")
            return

        balance = data.get("balance", data.get("balanceUsdc", "0"))

        # Convert from raw to human-readable (6 decimals)
        try:
            balance_human = f"{int(balance) / 1_000_000:.2f}"
        except (ValueError, TypeError):
            balance_human = str(balance)

        yield self.create_text_message(
            f"Vault {vault_address[:10]}...{vault_address[-4:]} balance: {balance_human} USDC"
        )
        yield self.create_json_message(
            {
                "vault": vault_address,
                "balance": balance_human,
                "balanceRaw": str(balance),
                "chainId": chain_id,
            }
        )
