from collections.abc import Generator
from typing import Any
import hashlib
import time
import uuid

import requests
from eth_account import Account

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class SwapTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        relayer_url = self.runtime.credentials["relayer_url"].rstrip("/")
        bot_private_key = self.runtime.credentials["bot_private_key"]
        vault_address = self.runtime.credentials["vault_address"]
        chain_id = int(self.runtime.credentials["chain_id"])

        from_token = tool_parameters["from_token"]
        to_token = tool_parameters["to_token"]
        amount_human = tool_parameters["amount"]
        memo = tool_parameters.get("memo", "")

        # Convert human amount to raw (assume 6 decimals for most stablecoins)
        try:
            amount_raw = str(int(float(amount_human) * 1_000_000))
        except ValueError:
            yield self.create_text_message(f"Invalid amount: {amount_human}")
            return

        bot_account = Account.from_key(bot_private_key)
        deadline = int(time.time()) + 900

        ref = (
            "0x"
            + hashlib.sha256(
                (memo or f"dify-swap-{uuid.uuid4().hex[:8]}").encode()
            ).hexdigest()
        )

        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "SwapIntent": [
                    {"name": "bot", "type": "address"},
                    {"name": "fromToken", "type": "address"},
                    {"name": "toToken", "type": "address"},
                    {"name": "maxFromAmount", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "ref", "type": "bytes32"},
                ],
            },
            "primaryType": "SwapIntent",
            "domain": {
                "name": "AxonVault",
                "version": "1",
                "chainId": chain_id,
                "verifyingContract": vault_address,
            },
            "message": {
                "bot": bot_account.address,
                "fromToken": from_token,
                "toToken": to_token,
                "maxFromAmount": int(amount_raw),
                "deadline": deadline,
                "ref": ref,
            },
        }

        signed = Account.sign_typed_data(
            bot_account.key,
            domain_data=typed_data["domain"],
            message_types={"SwapIntent": typed_data["types"]["SwapIntent"]},
            message_data=typed_data["message"],
        )

        payload = {
            "bot": bot_account.address,
            "fromToken": from_token,
            "toToken": to_token,
            "maxFromAmount": amount_raw,
            "deadline": str(deadline),
            "ref": ref,
            "signature": "0x" + signed.signature.hex(),
            "chainId": chain_id,
            "vaultAddress": vault_address,
            "idempotencyKey": uuid.uuid4().hex,
            "memo": memo or None,
        }

        try:
            resp = requests.post(f"{relayer_url}/v1/swap", json=payload, timeout=30)
            data = resp.json()
        except Exception as e:
            yield self.create_text_message(f"Swap request failed: {e}")
            return

        if resp.status_code >= 400:
            error = data.get("message", data.get("error", resp.text))
            yield self.create_text_message(f"Swap rejected: {error}")
            return

        result = {
            "status": data.get("status", "submitted"),
            "requestId": data.get("requestId"),
            "txHash": data.get("txHash"),
            "fromToken": from_token,
            "toToken": to_token,
            "amount": amount_human,
        }

        if data.get("txHash"):
            yield self.create_text_message(
                f"Swap complete! {amount_human} swapped. TX: {data['txHash']}"
            )
        else:
            yield self.create_text_message(
                f"Swap submitted (status: {data.get('status', 'pending')}). "
                f"Request ID: {data.get('requestId')}."
            )

        yield self.create_json_message(result)
