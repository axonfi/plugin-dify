from collections.abc import Generator
from typing import Any

import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class GetVaultValueTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        relayer_url = self.runtime.credentials["relayer_url"].rstrip("/")
        vault_address = self.runtime.credentials["vault_address"]
        chain_id = self.runtime.credentials["chain_id"]

        try:
            resp = requests.get(
                f"{relayer_url}/v1/vault/{vault_address}/value",
                params={"chainId": chain_id},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            yield self.create_text_message(f"Failed to fetch vault value: {e}")
            return

        total = data.get("totalValueUsd", 0)
        tokens = data.get("tokens", [])

        lines = [f"Vault total value: ${total:.2f}"]
        for t in tokens:
            symbol = t.get("symbol", t.get("token", "?")[:8])
            value = t.get("valueUsd", 0)
            balance_raw = int(t.get("balance", "0"))
            decimals = t.get("decimals", 18)
            balance_human = balance_raw / (10 ** decimals)
            lines.append(f"  {symbol}: {balance_human:.6g} (${value:.2f})")

        yield self.create_text_message("\n".join(lines))
        yield self.create_json_message(data)
