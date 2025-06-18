# Masumi Agent

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/oX6NvX?referralCode=pa1ar)

## Setup

```bash
cp .env.example .env
# edit .env with your config

uv venv
source .venv/bin/activate
uv pip sync requirements.txt

python get_payment_source_info.py
# add SELLER_VKEY to .env
```

## Run

```bash
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
