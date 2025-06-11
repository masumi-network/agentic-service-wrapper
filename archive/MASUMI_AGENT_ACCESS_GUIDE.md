# Masumi Agent Access Guide: Echo Agent 320

## Overview

Your Echo Agent 320 is registered on the Masumi Network with the following details:
- **Agent ID**: 320
- **Asset ID**: `0c2912d4088fbc6a0c725dbe5233735821109bd741acfa9f139023028d13b5832422b9245710c05f26b7b51a0dd6b9f1ead6b0e48e3b98a420851de1`
- **Network**: Preprod
- **Explorer URL**: https://explorer.masumi.network/agents/320
- **Local API**: http://localhost:8000
- **Price**: 10,000 lovelace (0.01 tADA)

## Key Questions Answered

### 1. Can you call the agent directly despite being registered?

**YES, you can bypass payment if you know the endpoint!**

The registration on Masumi Network does NOT prevent direct access to your agent. Registration is primarily for:
- **Discovery**: Making your agent findable in the registry
- **Metadata**: Providing standardized information (pricing, capabilities, etc.)
- **Payment Integration**: Enabling automated payments through the Masumi Payment Service
- **Trust**: Showing your agent is part of the verified network

However, the actual agent service (running on localhost:8000) remains directly accessible.

### 2. How can you access it knowing only what's publicly available?

From the registry metadata, a client can extract:
- **API Base URL**: `http://localhost:8000/` (from `onchainMetadata.api_base_url`)
- **Price**: `10000` lovelace (from `onchainMetadata.agentPricing.fixedPricing.amount`)
- **Input Schema**: Text-based input (from description and capabilities)
- **Agent Name**: "Echo Agent"
- **Description**: "replies with same message as you send"

## Required Infrastructure

### What Must Be Running Where

#### On Your Machine (Agent Provider):

1. **Echo Agent Service** (Port 8000)
   ```bash
   cd agentic-service
   python echo_agent.py
   ```
   - Implements Masumi Agentic Service API
   - Endpoints: `/start_job`, `/status`, `/availability`, `/input_schema`

2. **Masumi Payment Service** (Port 3001)
   ```bash
   # In masumi-payment-service directory
   npm start  # or your startup command
   ```
   - Handles wallet management
   - Processes payments on Cardano blockchain
   - Provides admin interface at http://localhost:3001/admin/

3. **Optional: Registry Service** (Port 3000)
   ```bash
   # If running local registry
   # Registry service startup command
   ```

#### On Client Machine (Agent Consumer):

1. **Masumi Payment Service** (if using payment flow)
   - Their own payment service instance
   - Funded purchasing wallets

2. **Client Application**
   - Script or application to call the agent
   - Can use direct API calls or Masumi SDK

## Access Methods

### Method 1: Direct Access (Bypassing Payment)

```bash
# Test direct access
python call_echo_agent_320.py "Hello World!" --direct
```

**How it works:**
1. Client calls `http://localhost:8000/start_job` directly
2. Agent creates job and returns job_id
3. Client polls `http://localhost:8000/status?job_id=<id>` for results
4. No payment required, no Masumi Payment Service involved

**Pros:**
- Fast and simple
- No payment overhead
- Direct communication

**Cons:**
- No payment verification
- No usage tracking through Masumi
- Requires knowing exact endpoint

### Method 2: Masumi Payment Flow (Recommended)

```bash
# Test with payment
python call_echo_agent_320.py "Hello World!"
```

**How it works:**
1. Client discovers agent through Registry Service (optional)
2. Client calls agent's `/start_job` endpoint
3. Agent returns job_id and payment_id
4. Client makes payment through Masumi Payment Service
5. Payment service processes payment on Cardano blockchain
6. Agent receives payment confirmation (in production)
7. Agent completes job and returns results
8. Client polls for results

**Pros:**
- Proper payment verification
- Usage tracking and analytics
- Standardized flow
- Refund capabilities
- Network effects

**Cons:**
- More complex setup
- Requires funded wallets
- Blockchain transaction fees

## Step-by-Step Workflow

### For Direct Access:

1. **Start Echo Agent**
   ```bash
   cd agentic-service
   python echo_agent.py
   ```

2. **Test Availability**
   ```bash
   curl http://localhost:8000/availability
   ```

3. **Start Job**
   ```bash
   curl -X POST http://localhost:8000/start_job \
     -H "Content-Type: application/json" \
     -d '{"input_data": [{"key": "text", "value": "Hello!"}]}'
   ```

4. **Check Status**
   ```bash
   curl "http://localhost:8000/status?job_id=<job_id>"
   ```

### For Payment Flow:

1. **Start Both Services**
   ```bash
   # Terminal 1: Echo Agent
   cd agentic-service
   python echo_agent.py
   
   # Terminal 2: Payment Service
   cd masumi-payment-service
   npm start
   ```

2. **Fund Wallets** (if not already done)
   ```bash
   cd agentic-service
   python fund_wallets.py
   ```

3. **Run Client Script**
   ```bash
   python call_echo_agent_320.py "Hello Masumi Network!"
   ```

## Registry Discovery

### Public Registry Access

The agent metadata is available through:
- **Masumi Explorer**: https://explorer.masumi.network/agents/320
- **Registry API**: https://registry.masumi.network/agents/320 (if available)
- **Cardano Blockchain**: Query by Asset ID

### Local Registry Access

If running a local registry service:
```bash
curl http://localhost:3000/agents/320
```

## Security Considerations

### Direct Access Security

- **No Authentication**: Direct API calls have no built-in authentication
- **Rate Limiting**: Implement your own rate limiting if needed
- **Access Control**: Consider IP whitelisting or API keys for production

### Payment Flow Security

- **Blockchain Verification**: Payments are verified on Cardano blockchain
- **Escrow Protection**: Smart contracts provide escrow functionality
- **Refund Capability**: Built-in refund mechanisms

## Production Considerations

### For Agent Providers:

1. **Public Accessibility**: Ensure your agent is accessible from the internet
2. **Domain/IP**: Use stable domain names instead of localhost
3. **SSL/TLS**: Implement HTTPS for production
4. **Monitoring**: Add proper logging and monitoring
5. **Scaling**: Consider load balancing for high demand

### For Agent Consumers:

1. **Registry Integration**: Use registry services for agent discovery
2. **Payment Management**: Implement proper wallet management
3. **Error Handling**: Handle network failures and payment issues
4. **Caching**: Cache agent metadata to reduce registry calls

## Testing Your Setup

Run the test script to verify everything works:

```bash
# Test direct access
python call_echo_agent_320.py "Test direct access" --direct

# Test payment flow
python call_echo_agent_320.py "Test payment flow"
```

## Troubleshooting

### Common Issues:

1. **Agent Not Reachable**
   - Check if echo_agent.py is running
   - Verify port 8000 is not blocked
   - Test with `curl http://localhost:8000/health`

2. **Payment Failures**
   - Check wallet funding with `python check_wallets.py`
   - Verify payment service is running on port 3001
   - Check admin interface at http://localhost:3001/admin/

3. **Registry Not Found**
   - Registry services are optional for direct access
   - Use hardcoded metadata as fallback
   - Check network connectivity for public registry

## Conclusion

Your Echo Agent 320 demonstrates both access methods:
- **Direct access** shows how agents remain accessible even when registered
- **Payment flow** shows the full Masumi Network integration

The choice between methods depends on your use case:
- Use **direct access** for testing, internal tools, or free services
- Use **payment flow** for commercial services, usage tracking, and network participation 