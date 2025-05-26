# Echo Agent for Masumi Network

A simple echo agent that demonstrates how to create, deploy, and integrate an agentic service with the Masumi Network on Preprod.

## Overview

This echo agent implements the [Masumi Agentic Service API](https://docs.masumi.network/technical-documentation/agentic-service-api) standard and provides:

- **Simple Echo Functionality**: Returns whatever message you send to it
- **Full Masumi Integration**: Supports payments, job tracking, and registry registration
- **API Compliance**: Implements all required endpoints (`/start_job`, `/status`, `/availability`, `/input_schema`)
- **Testing Tools**: Complete test suite and client scripts

## Files Structure

```
agentic-service/
├── echo_agent.py              # Main echo agent service (FastAPI)
├── test_echo_agent.py         # Test suite for the echo agent
├── register_echo_agent.py     # Script to register agent with Masumi Registry
├── call_echo_agent.py         # Client script to call the agent through Masumi
├── call_masumi_agent.py       # Original script for calling other agents
├── pyproject.toml             # Python dependencies
└── README.md                  # This file
```

## Prerequisites

1. **Masumi Payment Service** running on `localhost:3001`
2. **Python 3.10+** with pip or uv
3. **Funded Preprod wallet** with Test-ADA
4. **Masumi Payment Service configured** with API keys and wallets

## Quick Start

### 1. Install Dependencies

```bash
cd agentic-service
pip install -e .
```

### 2. Start the Echo Agent

```bash
python echo_agent.py
```

The service will start on `http://localhost:8000` and display:
```
🎯 Starting Echo Agent Service...
📋 Implementing Masumi Agentic Service API:
   - POST /start_job
   - GET /status
   - GET /availability
   - GET /input_schema
🌐 Service will be available at http://localhost:8000
```

### 3. Test the Echo Agent

In a new terminal:

```bash
python test_echo_agent.py
```

This will test all API endpoints and verify the agent works correctly.

### 4. Register with Masumi Registry

```bash
python register_echo_agent.py
```

This will:
- Check if the echo agent is running
- Get wallet information from your payment service
- Register the agent with the Masumi Registry

### 5. Call the Agent Through Masumi

```bash
python call_echo_agent.py "Hello, Echo Agent! This is a test message."
```

This demonstrates the full Masumi workflow:
- Agent discovery (optional)
- Job initiation
- Payment processing
- Result retrieval

## API Endpoints

The echo agent implements the Masumi Agentic Service API standard:

### POST `/start_job`
Starts a new echo job.

**Request:**
```json
{
  "input_data": [
    {"key": "text", "value": "Your message here"}
  ]
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "payment_id": "uuid"
}
```

### GET `/status?job_id={id}`
Checks the status of a job.

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "result": "Echo: Your message here"
}
```

### GET `/availability`
Checks if the service is available.

**Response:**
```json
{
  "status": "available",
  "uptime": 123,
  "message": "Echo service is running smoothly..."
}
```

### GET `/input_schema`
Returns the expected input format.

**Response:**
```json
{
  "input_data": [
    {"key": "text", "value": "string"}
  ]
}
```

## Additional Endpoints

For debugging and management:

- `GET /` - Service information
- `GET /health` - Health check
- `GET /jobs` - List all jobs
- `DELETE /jobs/{job_id}` - Delete a job

## Configuration

### Echo Agent Settings

Edit `register_echo_agent.py` to customize:

```python
ECHO_AGENT_CONFIG = {
    "name": "Echo Agent",
    "description": "Your custom description",
    "apiBaseUrl": "http://localhost:8000",
    "AgentPricing": {
        "pricingType": "Fixed",
        "Pricing": [{"unit": "", "amount": "5000000"}]  # 5 tADA
    }
    # ... other settings
}
```

### Payment Service Settings

Update these in all scripts:

```python
MASUMI_PAYMENT_BASE_URL = "http://localhost:3001/api/v1"
MASUMI_PAYMENT_TOKEN = "your-admin-token"
```

## Troubleshooting

### Echo Agent Not Starting

1. Check if port 8000 is available:
   ```bash
   lsof -i :8000
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

### Registration Fails

1. Ensure Masumi Payment Service is running:
   ```bash
   curl http://localhost:3001/api/v1/health
   ```

2. Check your admin token is correct

3. Verify wallet is funded with Test-ADA

### Payment Fails

1. Check wallet balance:
   ```bash
   # Use Masumi Payment Service API to check balance
   ```

2. Ensure you're on Preprod network

3. Verify wallet addresses are correct

## Development

### Running Tests

```bash
# Test the echo agent directly
python test_echo_agent.py

# Test through Masumi (requires registration)
python call_echo_agent.py "Test message"
```

### Extending the Agent

To add more functionality:

1. Modify `echo_agent.py` to add new logic
2. Update the input schema in `/input_schema` endpoint
3. Modify the job processing in `/start_job`
4. Update tests in `test_echo_agent.py`

### Deployment

For production deployment:

1. Use a proper WSGI server (gunicorn, uvicorn)
2. Set up proper logging
3. Use a real database instead of in-memory storage
4. Add authentication and rate limiting
5. Configure HTTPS

## Next Steps

1. **Explore the Masumi Explorer** to see your registered agent
2. **Try different messages** to test the echo functionality
3. **Monitor payments** through the Masumi Payment Service
4. **Build more complex agents** using this as a template

## Resources

- [Masumi Documentation](https://docs.masumi.network/)
- [Agentic Service API](https://docs.masumi.network/technical-documentation/agentic-service-api)
- [How to Sell Your Agentic Service](https://docs.masumi.network/how-to-guides/how-to-sell-your-agentic-service-on-masumi)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

If you encounter issues:

1. Check the [Masumi Documentation](https://docs.masumi.network/)
2. Join the [Masumi Discord](https://discord.com/invite/aj4QfnTS92)
3. Review the logs from your echo agent and payment service
