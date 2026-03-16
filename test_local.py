"""Quick local test — validates EIP-712 signing and relayer submission without Dify runtime."""

import hashlib
import os
import time
import uuid
import requests
from eth_account import Account

RELAYER_URL = "https://relay.axonfi.xyz"

# Base Sepolia test vault — update these
VAULT_ADDRESS = "0x05c6ab8c7b0b1bb42980d9b6a4cb666f0af424c7"
CHAIN_ID = 84532
USDC = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

BOT_PRIVATE_KEY = os.environ.get("BOT_PRIVATE_KEY", "")


def test_health():
    resp = requests.get(f"{RELAYER_URL}/health", timeout=10)
    data = resp.json()
    print(f"Health: {data['status']} (db: {data['database']}, redis: {data['redis']})")
    assert data["status"] == "ok"


def test_pay(to: str, amount_human: str, memo: str = "dify-test"):
    if not BOT_PRIVATE_KEY:
        print("Set BOT_PRIVATE_KEY to test payments")
        return

    bot = Account.from_key(BOT_PRIVATE_KEY)
    amount_raw = int(float(amount_human) * 1_000_000)
    deadline = int(time.time()) + 900
    ref = "0x" + hashlib.sha256(memo.encode()).hexdigest()

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
        "domain": {
            "name": "AxonVault",
            "version": "1",
            "chainId": CHAIN_ID,
            "verifyingContract": VAULT_ADDRESS,
        },
        "message": {
            "bot": bot.address,
            "to": to,
            "token": USDC,
            "amount": amount_raw,
            "deadline": deadline,
            "ref": ref,
        },
    }

    signed = Account.sign_typed_data(
        bot.key,
        domain_data=typed_data["domain"],
        message_types={"PaymentIntent": typed_data["types"]["PaymentIntent"]},
        message_data=typed_data["message"],
    )

    payload = {
        "bot": bot.address,
        "to": to,
        "token": USDC,
        "amount": str(amount_raw),
        "deadline": str(deadline),
        "ref": ref,
        "signature": "0x" + signed.signature.hex(),
        "chainId": CHAIN_ID,
        "vaultAddress": VAULT_ADDRESS,
        "idempotencyKey": uuid.uuid4().hex,
        "memo": memo,
    }

    print(f"Sending {amount_human} USDC to {to}...")
    resp = requests.post(f"{RELAYER_URL}/v1/payments", json=payload, timeout=30)
    data = resp.json()

    if resp.status_code >= 400:
        print(f"Rejected: {data.get('message', data)}")
    else:
        print(f"Status: {data.get('status')}")
        if data.get("txHash"):
            print(f"TX: {data['txHash']}")
        if data.get("requestId"):
            print(f"Request ID: {data['requestId']}")

    return data


if __name__ == "__main__":
    test_health()
    # Send 0.10 USDC to deployer wallet as test
    test_pay("0xD8f5dbF83236fBe7B77E52F874f378ff52e904E0", "0.10", "dify-plugin-test")
