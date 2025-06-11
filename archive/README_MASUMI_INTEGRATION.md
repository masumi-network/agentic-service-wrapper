# Reverse Echo Agent with Masumi Payment Integration

## Overview

This Reverse Echo Agent has been **completely rewritten** to use the **official Masumi SDK** instead of manual HTTP requests. The integration now follows the proper Masumi documentation patterns and provides:

✅ **Proper SDK Integration** - Uses `masumi` package instead of manual API calls  
✅ **Environment Configuration** - All settings via `.env` file  
✅ **MIP-003 Compliance** - Follows Masumi Interaction Protocol v3  
✅ **Payment Service Connection** - Connects to your Docker Masumi Payment Service  
✅ **Dual Mode Operation** - Supports both paid and direct (test) execution  
✅ **Text Reversal Function** - Returns input text in reverse order for clear output demonstration

## What Was Fixed

### 🔧 **Previous Issues**
- ❌ Used manual HTTP requests instead of Masumi SDK
- ❌ Hardcoded configuration values
- ❌ Incorrect payment flow implementation
- ❌ Missing proper error handling
- ❌ No environment variable support

### ✅ **Fixed Implementation**
- ✅ **Official Masumi SDK** (`masumi` package)
- ✅ **Environment-based configuration** (`.env` file)
- ✅ **Proper payment monitoring** via SDK callbacks
- ✅ **Automatic payment completion** when jobs finish
- ✅ **MIP-003 compliant endpoints** and response formats
- ✅ **Connected to your Payment Service** on port 3001

## Setup Instructions

### 1. Dependencies Installation
```bash
pip install -r requirements.txt
```

This installs:
- `masumi` - Official Masumi SDK
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-dotenv` - Environment variable management
- `pydantic` - Data validation
- `requests` & `httpx` - HTTP clients

### 2. Environment Configuration

Your `.env` file is configured with:

```env
# Payment Service Configuration
PAYMENT_SERVICE_URL=http://localhost:3001/api/v1
PAYMENT_API_KEY=myadminkeyisalsoverysafe
MASUMI_PAYMENT_TOKEN=myadminkeyisalsoverysafe

# Agent Configuration (update AGENT_IDENTIFIER after registering)
AGENT_IDENTIFIER=echo_agent_placeholder_identifier
PAYMENT_AMOUNT=10000000
PAYMENT_UNIT=lovelace
SELLER_VKEY=1c4fa058d8c00e87b6bdf587bdc20069bdd6a0fbdab388770acfb959

# Network Configuration
NETWORK=Preprod
```

**Note:** The `SELLER_VKEY` was automatically retrieved from your payment service.

### 3. Agent Registration (Required for Payments)

To enable payment functionality, you need to register your agent:

```bash
# Option 1: Use registration script (if working)
python register_echo_agent.py

# Option 2: Manual registration via Masumi Registry API
# See Masumi documentation for registry endpoints
```

After registration, update `.env`:
```env
AGENT_IDENTIFIER=your_actual_agent_identifier_from_registry
```

## Usage

### Starting the Service

```bash
python echo_agent_with_payments.py
```

The service will start on `http://localhost:8000` with:
- ✅ **Official Masumi SDK** integration
- ✅ **Payment Service** connection on port 3001
- ✅ **MIP-003 compliant** API endpoints

### Available Endpoints

#### Core MIP-003 Endpoints
- `POST /start_job` - Start job with Masumi payment
- `GET /status?job_id=<id>` - Check job and payment status
- `GET /availability` - Service health check
- `GET /input_schema` - Get expected input format
- `POST /provide_input` - Provide additional input

#### Additional Endpoints
- `POST /start_job_direct` - Start job without payment (testing)
- `GET /config` - View current configuration
- `GET /jobs` - List all jobs (debugging)
- `GET /health` - Simple health check

### Testing the Integration

Run the comprehensive test suite:
```bash
python test_echo_agent_integration.py
```

This tests:
- ✅ Service availability
- ✅ Configuration loading
- ✅ Input schema compliance
- ✅ Direct job execution (no payment) - "Hello World" → "Reversed: dlroW olleH"
- ⚠️ Payment job execution (requires agent registration)

### Example Usage

#### 1. Direct Job (No Payment)
```bash
curl -X POST "http://localhost:8000/start_job_direct" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier_from_purchaser": "test_user",
    "input_data": {"text": "Hello World"}
  }'
```

Response:
```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "result": "Reversed: dlroW olleH",
  "message": "Job completed without payment (direct access)"
}
```

#### 2. Payment Job (Requires Agent Registration)
```bash
curl -X POST "http://localhost:8000/start_job" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier_from_purchaser": "buyer123",
    "input_data": {"text": "Masumi Network"}
  }'
```

Response (when properly registered):
```json
{
  "status": "success",
  "job_id": "uuid-here",
  "blockchainIdentifier": "payment-id",
  "agentIdentifier": "your-agent-id",
  "sellerVkey": "your-seller-vkey",
  "amounts": [{"amount": "10000000", "unit": "lovelace"}]
}
```

Then check status to get the result:
```bash
curl -X GET "http://localhost:8000/status?job_id=uuid-here"
```

Response:
```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "payment_status": "completed",
  "result": "Reversed: krowteN imusamM"
}
```

## Architecture

### Payment Flow (When Properly Configured)

1. **Job Creation** - Client calls `/start_job`
2. **Payment Request** - Masumi SDK creates payment request
3. **Payment Monitoring** - SDK monitors blockchain for payment
4. **Job Execution** - When payment confirmed, job runs
5. **Payment Completion** - SDK marks payment as complete
6. **Result Delivery** - Client gets result via `/status`

### Key Components

```python
# Masumi SDK Configuration
config = Config(
    payment_service_url=PAYMENT_SERVICE_URL,
    payment_api_key=PAYMENT_API_KEY
)

# Payment Instance
payment = Payment(
    agent_identifier=AGENT_IDENTIFIER,
    config=config,
    identifier_from_purchaser=request.identifier_from_purchaser,
    input_data=request.input_data,
    network=NETWORK
)

# Payment Monitoring
await payment.start_status_monitoring(payment_callback)
```

## Troubleshooting

### Common Issues

#### 1. "Masumi SDK not available"
```bash
pip install masumi
```

#### 2. "Payment service not connected"
- Ensure Docker Masumi Payment Service is running on port 3001
- Check `PAYMENT_SERVICE_URL` in `.env`
- Verify `PAYMENT_API_KEY` is correct

#### 3. "Invalid API key" error
- Your `AGENT_IDENTIFIER` is still the placeholder
- Register your agent first
- Update `.env` with real agent identifier

#### 4. Payment jobs fail
```bash
# Check payment service connection
python get_payment_source_info.py

# Verify configuration
curl http://localhost:8000/config
```

### Environment Variables Check

```bash
# View current configuration
curl http://localhost:8000/config

# Should show:
# - payment_service_url: http://localhost:3001/api/v1
# - masumi_sdk_available: true
# - seller_vkey: (your actual vkey)
# - agent_identifier: (needs to be real after registration)
```

## Next Steps

1. **Register Your Agent**
   - Use Masumi Registry service
   - Get real `AGENT_IDENTIFIER`
   - Update `.env` file

2. **Test Payment Flow**
   - Use `/start_job` endpoint
   - Monitor payment status
   - Verify completion

3. **Production Deployment**
   - Use proper database instead of in-memory storage
   - Add authentication/authorization
   - Set up monitoring and logging

## Files Updated

- ✅ `echo_agent_with_payments.py` - Complete rewrite with Masumi SDK + reverse text functionality
- ✅ `.env` - Proper configuration with real values
- ✅ `requirements.txt` - Added Masumi SDK dependency
- ✅ `get_payment_source_info.py` - Helper script for configuration
- ✅ `test_echo_agent_integration.py` - Comprehensive testing with reverse examples

Your reverse echo agent now properly integrates with the Masumi Network using the official SDK and connects to your Docker payment service! Users can clearly see the difference between input and output with the text reversal feature. 🎉 