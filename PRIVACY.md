# Privacy Policy

The AxonFi Dify plugin sends payment requests to the AxonFi relayer API. The following data is transmitted:

- Bot public address (derived from the private key)
- Recipient address
- Payment amount and token
- Vault address
- Chain ID
- Optional memo text

No data is stored by the plugin itself. Payment data is processed by the AxonFi relayer according to the [AxonFi Privacy Policy](https://axonfi.xyz/privacy).

The bot private key is stored locally in your Dify instance credentials and is never transmitted — only the generated signature is sent to the relayer.
