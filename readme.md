# Agentic Service Wrapper - CrewAI Branch

Masumi-compliant agent service with CrewAI integration for the Masumi Network.

## Quick Start

```bash
# Setup environment
cp .env.example .env
# Add your OpenAI API key to .env

# Install dependencies
uv venv && source .venv/bin/activate
uv pip sync requirements.txt

# Test the service
uv run python agentic_service.py --input "Hello world" --verbose

# Start API server
uv run python main.py api
```

## Configuration

### Required Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4.1-nano  # default: gpt-4.1-nano (cheapest, fastest)

# Masumi Network Configuration
PAYMENT_SERVICE_URL=http://localhost:3001/api/v1
PAYMENT_API_KEY=your-payment-api-key
AGENT_IDENTIFIER=your-agent-identifier
SELLER_VKEY=your-seller-wallet-vkey
NETWORK=Preprod
```

## Customization

The service is designed for easy customization:

- **Crew Logic**: Edit `crew.py` for CrewAI agents and tasks
- **Agent Config**: Modify `config/agents.yaml` 
- **Task Config**: Modify `config/tasks.yaml`
- **Model Settings**: Change `OPENAI_MODEL` environment variable

## Testing

```bash
# Test CrewAI integration
uv run python -m pytest test_api.py::TestCrewAIIntegration -v

# Test Masumi compliance
uv run python -m pytest test_api.py::TestMasumiCompliance -v

# Run all tests
uv run python -m pytest test_api.py -v
```

## API Endpoints

### Core Endpoints (Masumi Standard)

- `POST /start_job` - Start new job with payment integration
- `GET /status?job_id=<id>` - Check job status
- `GET /availability` - Server availability
- `GET /input_schema` - Input format schema
- `GET /health` - Health check

### Example Usage

```bash
# Start a job
curl -X POST http://localhost:8000/start_job \
  -H "Content-Type: application/json" \
  -d '{"input_data": [{"key": "input_string", "value": "Analyze this text"}]}'

# Check status
curl "http://localhost:8000/status?job_id=your-job-id"
```

## Railway Deployment

### 1. Deploy Masumi Payment Service

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/masumi-payment-service-official?referralCode=padierfind)

- Provide Blockfrost API key
- Generate public URL after deployment
- Note the URL format: `https://your-service.railway.app/api/v1`

### 2. Deploy Agent Service

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/masumi-compliant-service-api-official?referralCode=padierfind)

- Set `PAYMENT_SERVICE_URL` to your payment service
- Add `OPENAI_API_KEY` for full functionality
- Configure other environment variables

### 3. Register Agent

- Access payment service admin panel
- Register agent using your service URL
- Update agent service with `AGENT_IDENTIFIER` and `SELLER_VKEY`

## Architecture

This branch demonstrates multi-integration capabilities using git branches:

- **main** - Minimal reverse echo service (zero dependencies)
- **crewai** - CrewAI integration (this branch)  
- **langchain** - LangChain integration (planned)
- **n8n** - n8n workflow integration (planned)

Each branch maintains Masumi compliance while showcasing different AI frameworks.

## Development

```bash
# Direct service testing
uv run python agentic_service.py --input "test" --verbose

# Local development
uv run python main.py api

# Validate configuration
python get_payment_source_info.py
```

For detailed Masumi Network documentation, visit [docs.masumi.network](https://docs.masumi.network/).