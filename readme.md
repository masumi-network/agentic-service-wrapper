# Masumi Agent Service

## Railway Deployment

### Prerequisites
- Blockfrost API key
- For quick deployment: [Railway account](https://railway.com?referralCode=pa1ar) (free trial is 30 days or $5)

### How to Deploy

1. **Deploy Payment Service**:  
[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/1n00SW?referralCode=pa1ar)
   - Provide Blockfrost API key in variables (required to click "deploy")
   - Wait for database service to start
   - Go to database variables, copy `DATABASE_URL` value
   - Go to Payment Service variables, edit `DATABASE_URL` with copied value
   - Click deploy changes, wait for service to start
   - Generate public URL in Payment Service settings, copy URL
   - Test at public URL `/admin` or `/docs`

2. **Deploy Agent Service**:  
[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/KnOf66?referralCode=pa1ar)
   - Provide Payment Service URL in variables
   - Generate public URL, test at `/docs`

3. **Configure Agent**
   - Go to Payment Service admin panel, top up selling wallet
   - Register agent via Agent Service URL
   - Retrieve Agent ID
   - Go to Agent Service variables, add:
     - `SELLER_VKEY`: vkey of selling wallet used to register agent
     - `PAYMENT_API_KEY`: payment token or admin key for Payment Service
     - `PAYMENT_SERVICE_URL`: URL of your Payment Service

4. **Test Integration**
   - Start job via Agent Service
   - Copy job output (excluding job_id and payment_id)
   - Paste to `/purchase` on Payment Service
   - Check job status on Agent Service for results

## How to Customize

1. Fork this repository
2. Edit `agentic_service.py` to implement your agent logic
3. Update `input_schema` in main.py to match your input requirements
4. Run or deploy your customized version using the Railway (you will just need to replace the repository in settings of the service to point to your fork).

> **Side note:** Railway can try to deploy public repository without asking for any permissions. To deploy a private repository, you need to connect Railway to your GitHub account or GitHub organisation and grant reading permissions (you will be guided through the process by Railway).

## Local Setup

```bash
cp .env.example .env
# edit .env with your config

uv venv
source .venv/bin/activate
uv pip sync requirements.txt

python get_payment_source_info.py
# add SELLER_VKEY to .env

python main.py api
```

## API Endpoints

### `/start_job` - Start a new job
**POST** request with the following JSON body (Masumi Network Standard):

```json
{
  "input_data": [
    {"key": "input_string", "value": "Hello World"}
  ]
}
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "payment_id": "payment-identifier"
}
```

### Other Endpoints
- `GET /availability` - Check server status
- `GET /input_schema` - Get input schema definition
- `GET /status?job_id=<id>` - Check job status
- `GET /health` - Health check

## Test

```bash
# basic health checks
curl http://localhost:8000/availability
curl http://localhost:8000/input_schema

# start a job (Masumi Network format)
curl -X POST http://localhost:8000/start_job \
  -H "Content-Type: application/json" \
  -d '{"input_data": [{"key": "input_string", "value": "Hello World"}]}'

# run test suite
uv run python -m pytest test_api.py -v
```
