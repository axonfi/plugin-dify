# AxonFi Plugin for Dify

Non-custodial treasury and gasless payments for autonomous AI agents.

## Tools

- **Pay** — Send payments from your vault. EIP-712 signed, gasless.
- **Swap** — Rebalance tokens within your vault (e.g. USDC → WETH).
- **Execute Protocol** — Interact with DeFi protocols (Uniswap, Aave, etc.) through your vault.
- **Get Balance** — Check your vault's USDC balance.
- **Get Payment Status** — Poll the status of a submitted payment.
- **Get Swap Status** — Poll the status of a submitted swap.
- **Get Execute Status** — Poll the status of a protocol execution.

## Setup

1. Deploy a vault at [app.axonfi.xyz](https://app.axonfi.xyz)
2. Deposit USDC (or any ERC-20) to your vault
3. Register a bot and get its private key
4. Configure the plugin with your relayer URL, bot key, vault address, and chain

## Links

- [Documentation](https://axonfi.xyz/docs)
- [Dashboard](https://app.axonfi.xyz)
- [GitHub](https://github.com/axonfi)
- [SDK](https://www.npmjs.com/package/@axonfi/sdk)
