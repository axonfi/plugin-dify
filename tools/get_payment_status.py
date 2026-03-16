from collections.abc import Generator
from typing import Any

import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class GetPaymentStatusTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        relayer_url = self.runtime.credentials["relayer_url"].rstrip("/")
        request_id = tool_parameters["request_id"]

        try:
            resp = requests.get(
                f"{relayer_url}/v1/payments/{request_id}",
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            yield self.create_text_message(f"Failed to fetch payment status: {e}")
            return

        status = data.get("status", "unknown")
        tx_hash = data.get("txHash")
        reason = data.get("reason")

        msg = f"Payment {request_id}: {status}"
        if tx_hash:
            msg += f" | TX: {tx_hash}"
        if reason:
            msg += f" | Reason: {reason}"

        yield self.create_text_message(msg)
        yield self.create_json_message(data)
