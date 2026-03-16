# AxonFi Plugin for Dify

The treasury layer for autonomous AI agents. Deploy a single non-custodial vault, register your entire bot fleet, and let them pay, swap, and interact with DeFi — without ever touching private keys or gas.

## Why AxonFi

- **One vault, unlimited bots** — your entire agent fleet shares a single on-chain treasury. Each bot gets independent spending limits, destination whitelists, and per-transaction caps.
- **Gasless by design** — bots sign EIP-712 intents off-chain. AxonFi's relayer pays gas and executes on-chain. Your agents never need ETH.
- **Smart payment routing** — bots request payment in any token. If the vault holds USDC but the recipient wants WETH, the relayer swaps atomically. The bot doesn't know or care about routing.
- **HTTP 402 native** — agents can pay through 402 paywalls automatically, making them first-class participants in the pay-per-use API economy.
- **Full DeFi access** — agents interact with Uniswap, Aave, or any on-chain protocol through the vault using an approve-call-revoke pattern. Full DeFi, zero custody risk.
- **AI fraud detection** — suspicious transactions go through a 3-agent LLM consensus (safety + behavioral + reasoning). If the AI isn't sure, it escalates to human review with mobile push notifications.
- **Non-custodial** — the vault is a standalone smart contract. Only the owner can withdraw. Even if AxonFi disappears, your funds are safe on-chain.

## Tools

| Tool | Description |
|------|-------------|
| **Pay** | Send payments from your vault. Supports any ERC-20 with automatic swap routing. Gasless. |
| **Swap** | Rebalance tokens within the vault (e.g. USDC to WETH). Funds stay in the vault. |
| **Execute Protocol** | Call any DeFi protocol (Uniswap, Aave, Lido, etc.) through the vault with approve-call-revoke. |
| **Get Vault Value** | Get total USD value of your vault across all tokens + native ETH. |
| **Get Balance** | Check your vault's token balance (any ERC-20, defaults to USDC). |
| **Get Payment Status** | Poll the status of a submitted payment by request ID. |
| **Get Swap Status** | Poll the status of a submitted swap by request ID. |
| **Get Execute Status** | Poll the status of a protocol execution by request ID. |

## Supported Chains

- Base (mainnet)
- Arbitrum One (mainnet)
- Base Sepolia (testnet)
- Arbitrum Sepolia (testnet)

## Setup

1. Deploy a vault at [app.axonfi.xyz](https://app.axonfi.xyz)
2. Deposit USDC (or any ERC-20) to your vault
3. Register a bot and get its private key
4. Configure the plugin with your relayer URL, bot key, vault address, and chain

## Links

- [Website](https://axonfi.xyz)
- [Documentation](https://axonfi.xyz/docs)
- [Dashboard](https://app.axonfi.xyz)
- [GitHub](https://github.com/axonfi)
- [npm SDK](https://www.npmjs.com/package/@axonfi/sdk)
- [PyPI SDK](https://pypi.org/project/axonfi/)
