from collections.abc import Generator
from typing import Any
import hashlib
import time
import uuid

import requests
from eth_account import Account

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

# Known USDC addresses per chain
USDC = {
    "8453": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "42161": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    "84532": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "421614": "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d",
}


class PayTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        relayer_url = self.runtime.credentials["relayer_url"].rstrip("/")
        bot_private_key = self.runtime.credentials["bot_private_key"]
        vault_address = self.runtime.credentials["vault_address"]
        chain_id = int(self.runtime.credentials["chain_id"])

        to = tool_parameters["to"]
        amount_human = tool_parameters["amount"]
        token = tool_parameters.get("token") or USDC.get(str(chain_id))
        memo = tool_parameters.get("memo", "")

        if not token:
            yield self.create_text_message(
                f"No default USDC address for chain {chain_id}. Please specify a token address."
            )
            return

        # Convert human amount to raw (6 decimals for USDC)
        try:
            amount_raw = str(int(float(amount_human) * 1_000_000))
        except ValueError:
            yield self.create_text_message(f"Invalid amount: {amount_human}")
            return

        # Build EIP-712 PaymentIntent
        bot_account = Account.from_key(bot_private_key)
        deadline = int(time.time()) + 900  # 15 minutes

        ref = (
            "0x"
            + hashlib.sha256(
                (memo or f"dify-{uuid.uuid4().hex[:8]}").encode()
            ).hexdigest()
        )

        domain = {
            "name": "AxonVault",
            "version": "1",
            "chainId": chain_id,
            "verifyingContract": vault_address,
        }

        message = {
            "bot": bot_account.address,
            "to": to,
            "token": token,
            "amount": int(amount_raw),
            "deadline": deadline,
            "ref": ref,
        }

        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "PaymentIntent": [
                    {"name": "bot", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "ref", "type": "bytes32"},
                ],
            },
            "primaryType": "PaymentIntent",
            "domain": domain,
            "message": message,
        }

        signed = Account.sign_typed_data(
            bot_account.key,
            domain_data=typed_data["domain"],
            message_types={"PaymentIntent": typed_data["types"]["PaymentIntent"]},
            message_data=typed_data["message"],
        )

        # Submit to relayer
        payload = {
            "bot": bot_account.address,
            "to": to,
            "token": token,
            "amount": str(amount_raw),
            "deadline": str(deadline),
            "ref": ref,
            "signature": "0x" + signed.signature.hex(),
            "chainId": chain_id,
            "vaultAddress": vault_address,
            "idempotencyKey": uuid.uuid4().hex,
            "memo": memo or None,
        }

        try:
            resp = requests.post(
                f"{relayer_url}/v1/payments",
                json=payload,
                timeout=30,
            )
            data = resp.json()
        except Exception as e:
            yield self.create_text_message(f"Payment request failed: {e}")
            return

        if resp.status_code >= 400:
            error = data.get("message", data.get("error", resp.text))
            yield self.create_text_message(f"Payment rejected: {error}")
            return

        result = {
            "status": data.get("status", "submitted"),
            "requestId": data.get("requestId"),
            "txHash": data.get("txHash"),
            "amount": amount_human,
            "token": token,
            "to": to,
            "memo": memo,
        }

        if data.get("txHash"):
            yield self.create_text_message(
                f"Payment sent! {amount_human} to {to}. TX: {data['txHash']}"
            )
        else:
            yield self.create_text_message(
                f"Payment submitted (status: {data.get('status', 'pending')}). "
                f"Request ID: {data.get('requestId')}. Poll for status."
            )

        yield self.create_json_message(result)
