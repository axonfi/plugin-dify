from collections.abc import Generator
from typing import Any
import hashlib
import time
import uuid

import requests
from eth_account import Account

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class ExecuteProtocolTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        relayer_url = self.runtime.credentials["relayer_url"].rstrip("/")
        bot_private_key = self.runtime.credentials["bot_private_key"]
        vault_address = self.runtime.credentials["vault_address"]
        chain_id = int(self.runtime.credentials["chain_id"])

        protocol = tool_parameters["protocol"]
        calldata = tool_parameters["calldata"]
        token = tool_parameters["token"]
        amount = tool_parameters["amount"]
        value = tool_parameters.get("value", "0")
        memo = tool_parameters.get("memo", "")

        bot_account = Account.from_key(bot_private_key)
        deadline = int(time.time()) + 900

        ref = (
            "0x"
            + hashlib.sha256(
                (memo or f"dify-exec-{uuid.uuid4().hex[:8]}").encode()
            ).hexdigest()
        )

        # calldataHash = keccak256(calldata)
        from eth_utils import keccak

        calldata_bytes = bytes.fromhex(
            calldata[2:] if calldata.startswith("0x") else calldata
        )
        calldata_hash = "0x" + keccak(calldata_bytes).hex()

        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "ExecuteIntent": [
                    {"name": "bot", "type": "address"},
                    {"name": "protocol", "type": "address"},
                    {"name": "calldataHash", "type": "bytes32"},
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "value", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "ref", "type": "bytes32"},
                ],
            },
            "primaryType": "ExecuteIntent",
            "domain": {
                "name": "AxonVault",
                "version": "1",
                "chainId": chain_id,
                "verifyingContract": vault_address,
            },
            "message": {
                "bot": bot_account.address,
                "protocol": protocol,
                "calldataHash": calldata_hash,
                "token": token,
                "amount": int(amount),
                "value": int(value),
                "deadline": deadline,
                "ref": ref,
            },
        }

        signed = Account.sign_typed_data(
            bot_account.key,
            domain_data=typed_data["domain"],
            message_types={"ExecuteIntent": typed_data["types"]["ExecuteIntent"]},
            message_data=typed_data["message"],
        )

        payload = {
            "bot": bot_account.address,
            "protocol": protocol,
            "calldata": calldata,
            "calldataHash": calldata_hash,
            "token": token,
            "amount": str(amount),
            "value": str(value),
            "deadline": str(deadline),
            "ref": ref,
            "signature": "0x" + signed.signature.hex(),
            "chainId": chain_id,
            "vaultAddress": vault_address,
            "idempotencyKey": uuid.uuid4().hex,
            "memo": memo or None,
        }

        try:
            resp = requests.post(f"{relayer_url}/v1/execute", json=payload, timeout=30)
            data = resp.json()
        except Exception as e:
            yield self.create_text_message(f"Execute request failed: {e}")
            return

        if resp.status_code >= 400:
            error = data.get("message", data.get("error", resp.text))
            yield self.create_text_message(f"Execution rejected: {error}")
            return

        result = {
            "status": data.get("status", "submitted"),
            "requestId": data.get("requestId"),
            "txHash": data.get("txHash"),
            "protocol": protocol,
        }

        if data.get("txHash"):
            yield self.create_text_message(
                f"Protocol execution complete! TX: {data['txHash']}"
            )
        else:
            yield self.create_text_message(
                f"Execution submitted (status: {data.get('status', 'pending')}). "
                f"Request ID: {data.get('requestId')}."
            )

        yield self.create_json_message(result)
