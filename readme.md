# Masumi Agent Service

## Railway Deployment

> The purpose of this repository is to get you from 0 to agentic service owner in as little time as possible. Yet it is assumed, that you are somewhat familiar with [Masumi Network](https://masumi.network/). If you are not, please consider heading over to the official [Masumi docs](https://docs.masumi.network/) first.  

This example uses [Railway](https://railway.com?referralCode=pa1ar) templates. Railway is a cloud development platform that enables developers to deploy, manage and scale applications and databases with minimal configuration. Masumi Services obviously can be hosted anywhere, so feel free to use the templates as examples and pick a service of your choice.  

Railway templates we provide are pointing to the open-source repositories of Masumi organisation. That means you can read full code, if you want, to be sure nothing shady is going on. You can also fork the repositories first, and still use the templates by just pointing them to your forks, if you want.

### Prerequisites

- [Blockfrost](https://blockfrost.io/) API key
- For quick deployment: [Railway account](https://railway.com?referralCode=pa1ar) (free trial is 30 days or $5)

### How to Deploy

1. **Deploy [Masumi Payment Service](https://github.com/masumi-network/masumi-payment-service)**:  

    [![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/masumi-payment-service-official?referralCode=padierfind)
   - Use the template in an existing or new project (in existing project, "Create" > "Template" > search for "Masumi Payment Service")
   - Provide Blockfrost API key in variables (required to click "deploy")
   - Click on deploy, watch the logs, wait for it (takes 5+ minutes, depending on the load on Railway)
   - You should see 2 services on your canvas, connected with an dotted arrow: a PostgreSQL database and a Masumi Payment Service.
   - Click on Masumi Payment Service on the canvas > Settings > Networking > Generate URL
   - Test at public URL `/admin` or `/docs`. Your default admin key (used to login to the admin panel and sign transactions) is in your variables. **Change it on the admin panel.**
   - **Important:** Masumi API endpoints must include `/api/v1/`!  Be sure to append that slugs in the next steps (deploying agentic service).

2. **Deploy [Agent Service API Wrapper](https://github.com/masumi-network/agentic-service-wrapper)**:  

    [![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/masumi-compliant-service-api-official?referralCode=padierfind)
   - Make sure your Masumi payment service is up and running
   - Provide `PAYMENT_SERVICE_URL` in variables (format: `https://your-instance-of-masumi.up.railway.app/api/v1`, the main part of the URL can differ, point is - don't forget the `/api/v1` slugs)
   - Wait for deployment to complete
   - Generate public URL in settings of the service
   - Check the swagger at `/docs`

3. **Configure Agent**
   - Go to Payment Service admin panel, top up selling wallet
   - Register agent via Agent Service URL (you need to have funds on your selling wallet, read the [docs](https://docs.masumi.network/))
   - Retrieve Agent ID aka Asset ID
   - Check Agent Service variables:
     - `SELLER_VKEY`: vkey (verificatin key) of selling wallet used to register agent, get it from the admin panel of your payment service
     - `PAYMENT_API_KEY`: payment token or admin key for Payment Service (you have used it to login to the admin panel)
     - `PAYMENT_SERVICE_URL`: URL of your Payment Service

4. **Test Integration**
   - Start job via Agent Service
   - Copy job output (excluding `job_id` and `payment_id`)
   - Go to the `/docs` of your Masumi Payment Service
   - Open POST `/purchase` on Payment Service and paste your job output (this initiates the payment process)
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
