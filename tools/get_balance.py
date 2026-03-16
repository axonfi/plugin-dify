from collections.abc import Generator
from typing import Any

import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

# Known USDC addresses per chain
USDC = {
    "8453": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "42161": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    "84532": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "421614": "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d",
}


class GetBalanceTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        relayer_url = self.runtime.credentials["relayer_url"].rstrip("/")
        vault_address = self.runtime.credentials["vault_address"]
        chain_id = self.runtime.credentials["chain_id"]

        token = tool_parameters.get("token") or USDC.get(str(chain_id))
        decimals = int(tool_parameters.get("decimals") or 6)

        if not token:
            yield self.create_text_message(
                f"No default token for chain {chain_id}. Please specify a token address."
            )
            return

        try:
            resp = requests.get(
                f"{relayer_url}/v1/vaults/{vault_address}/balance",
                params={"chainId": chain_id, "token": token},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            yield self.create_text_message(f"Failed to fetch balance: {e}")
            return

        balance = data.get("balance", data.get("balanceUsdc", "0"))

        try:
            balance_human = f"{int(balance) / (10**decimals):.{min(decimals, 6)}f}"
        except (ValueError, TypeError):
            balance_human = str(balance)

        token_short = f"{token[:6]}...{token[-4:]}"
        yield self.create_text_message(
            f"Vault {vault_address[:10]}...{vault_address[-4:]} balance: {balance_human} ({token_short})"
        )
        yield self.create_json_message(
            {
                "vault": vault_address,
                "token": token,
                "balance": balance_human,
                "balanceRaw": str(balance),
                "decimals": decimals,
                "chainId": chain_id,
            }
        )
