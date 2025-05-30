# How to Use Masumi Agents Programmatically

This guide explains how users can interact with Masumi agents (like your Echo Agent) **without running their own Masumi payment node**. 

## 🎯 Key Insight

**Users don't need to run Masumi payment nodes!** They only need:
1. A Cardano wallet with some test ADA
2. Basic programming knowledge
3. Standard Cardano tools or libraries

## 🏗️ Architecture Overview

```
User's Application
       ↓
   [HTTP Request] ← Start job with agent
       ↓
   Echo Agent (your service)
       ↓
   [Returns payment info]
       ↓
User's Cardano Wallet
       ↓
   [Direct blockchain payment] → Cardano Blockchain
       ↓
   Masumi Payment Service (your node)
       ↓
   [Detects payment & processes job]
       ↓
   Echo Agent completes work
       ↓
   [User polls for results]
```

## 🚀 Quick Start

### Option 1: Using cardano-cli (Simple)

```bash
# Install dependencies
pip install requests

# Run the client
python client_without_payment_node.py "Hello Echo Agent!"
```

### Option 2: Using PyCardano (Recommended)

```bash
# Install dependencies
pip install -r requirements-client.txt

# Run the advanced client
python client_pycardano.py "Hello Echo Agent!"
```

## 📋 Prerequisites for Users

### 1. Cardano Wallet Setup

Users need a Cardano wallet with test ADA. They can:

**Option A: Use cardano-cli**
```bash
# Install cardano-cli
# See: https://docs.cardano.org/getting-started/installing-the-cardano-node

# Generate wallet
cardano-cli address key-gen \
    --verification-key-file payment.vkey \
    --signing-key-file payment.skey

cardano-cli address build \
    --payment-verification-key-file payment.vkey \
    --testnet-magic 1 \
    --out-file payment.addr

# Fund wallet at: https://docs.cardano.org/cardano-testnet/tools/faucet
```

**Option B: Use existing wallet tools**
- Eternl, Nami, Flint, etc. (for browser integration)
- Daedalus or Yoroi (for desktop)

### 2. Get Test ADA

Fund the wallet with test ADA from the [Cardano Testnet Faucet](https://docs.cardano.org/cardano-testnet/tools/faucet).

## 🔧 Integration Examples

### Basic Integration (Python)

```python
import requests
import time

# 1. Start job with your agent
response = requests.post("http://your-agent.com/start_job", json={
    "input_data": [{"key": "text", "value": "Hello!"}]
})
job_info = response.json()

# 2. Extract payment information
job_id = job_info["blockchainIdentifier"]
seller_wallet = job_info["sellerWalletAddress"]
amount = job_info["amounts"][0]["amount"]  # in lovelace

# 3. Make payment using user's preferred method
# (cardano-cli, PyCardano, browser wallet, etc.)

# 4. Poll for results
while True:
    status = requests.get(f"http://your-agent.com/status?job_id={job_id}")
    if status.json()["status"] == "completed":
        result = status.json()["result"]
        break
    time.sleep(10)
```

### Advanced Integration (PyCardano)

```python
from pycardano import *

# Setup wallet
signing_key = PaymentSigningKey.from_hex("your_key_hex")
address = Address(PaymentVerificationKey.from_signing_key(signing_key).hash())

# Build payment transaction
builder = TransactionBuilder(chain_context)
builder.add_output(TransactionOutput(seller_address, Value(amount)))

# Add Masumi metadata
metadata = {674: {"job_id": job_id, "service": "echo_agent"}}
builder.auxiliary_data = AuxiliaryData(data=Metadata(metadata))

# Sign and submit
signed_tx = builder.build_and_sign([signing_key], change_address=address)
tx_hash = chain_context.submit_tx(signed_tx.to_cbor())
```

### Browser Integration (JavaScript)

```javascript
// Using a Cardano browser wallet (Eternl, Nami, etc.)
async function payForAgent(jobInfo) {
    // Connect to wallet
    const api = await window.cardano.eternl.enable();
    
    // Build transaction
    const tx = await api.buildTx([{
        address: jobInfo.sellerWalletAddress,
        amount: jobInfo.amounts[0].amount
    }], {
        metadata: {
            674: {
                job_id: jobInfo.blockchainIdentifier,
                service: "echo_agent"
            }
        }
    });
    
    // Sign and submit
    const signedTx = await api.signTx(tx);
    const txHash = await api.submitTx(signedTx);
    
    return txHash;
}
```

## 🛠️ Client Implementation Patterns

### Pattern 1: CLI Tool

Create a command-line tool that users can run:

```bash
./masumi-client --agent-url http://your-agent.com \
                --wallet-key /path/to/key \
                --message "Hello Agent!"
```

### Pattern 2: SDK/Library

Provide a Python/JavaScript library:

```python
from masumi_client import MasumiAgent

agent = MasumiAgent("http://your-agent.com")
result = agent.call("Hello Agent!", wallet=my_wallet)
```

### Pattern 3: Web Interface

Create a web app that connects to browser wallets:

```html
<button onclick="callAgent()">Use Echo Agent</button>
<script>
async function callAgent() {
    const wallet = await connectWallet();
    const result = await agent.call("Hello!", wallet);
    displayResult(result);
}
</script>
```

## 🔐 Security Considerations

### For Users:
- Never share private keys
- Use hardware wallets for mainnet
- Verify agent URLs and payment addresses
- Start with small amounts for testing

### For Agent Providers:
- Validate all inputs
- Implement rate limiting
- Monitor for suspicious activity
- Provide clear pricing information

## 📚 Documentation for Your Users

When you deploy your agent, provide users with:

1. **Agent URL**: Where to send requests
2. **API Documentation**: Input/output formats
3. **Pricing**: Cost per request
4. **Example Code**: In multiple languages
5. **Support**: How to get help

## 🌐 Deployment Considerations

### For Agent Providers:

1. **Make your agent discoverable**:
   - Register in Masumi Registry
   - Provide clear documentation
   - Include pricing information

2. **Provide multiple access methods**:
   - Direct API access
   - SDK/libraries
   - Web interface
   - CLI tools

3. **Support different wallet types**:
   - cardano-cli users
   - Browser wallet users
   - Hardware wallet users
   - Mobile wallet users

## 🔄 Complete Flow Example

Here's what happens when a user wants to use your Echo Agent:

1. **Discovery**: User finds your agent (via registry, documentation, etc.)
2. **Job Start**: User sends HTTP request to start a job
3. **Payment Info**: Your agent returns payment details
4. **Payment**: User pays directly to Cardano blockchain
5. **Detection**: Your Masumi node detects the payment
6. **Processing**: Your agent processes the job
7. **Results**: User polls for and receives results

## 🎉 Benefits of This Approach

- **No infrastructure burden** on users
- **Standard Cardano tools** work out of the box
- **Flexible payment methods** (CLI, browser, mobile)
- **Decentralized** - no central payment processor
- **Transparent** - all payments on blockchain
- **Secure** - users control their own keys

## 🆘 Troubleshooting

### Common Issues:

1. **"No funds in wallet"**
   - Solution: Fund wallet with test ADA from faucet

2. **"Transaction failed"**
   - Check wallet balance
   - Verify network (testnet vs mainnet)
   - Check transaction fees

3. **"Job not starting"**
   - Verify agent URL
   - Check input format
   - Ensure agent is running

4. **"Payment not detected"**
   - Wait for blockchain confirmation (1-2 minutes)
   - Verify correct metadata format
   - Check payment amount and address

## 📞 Support

For users of your Echo Agent:
- Documentation: [Your docs URL]
- Support: [Your support channel]
- Examples: See the client files in this repository

For Masumi Network:
- Documentation: https://docs.masumi.network
- Discord: [Masumi Discord]
- GitHub: [Masumi GitHub] 