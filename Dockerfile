# Agentic Service Wrapper - CrewAI Branch
# Docker image for Railway deployment with environment variable documentation

FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install uv for faster dependency management
RUN pip install uv

# Install dependencies
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements.txt

# Copy application code
COPY . .

# Environment variables with placeholder defaults for documentation
# Railway will override these with actual values from the Variables tab
ENV OPENAI_API_KEY="your-openai-api-key-here"
ENV PAYMENT_SERVICE_URL="https://your-payment-service.railway.app/api/v1"
ENV PAYMENT_API_KEY="your-payment-api-key"
ENV AGENT_IDENTIFIER="your-agent-identifier"
ENV SELLER_VKEY="your-seller-wallet-vkey"
ENV NETWORK="Preprod"
ENV PORT="8000"
ENV CREWAI_TELEMETRY_OPT_OUT="true"

# Expose port
EXPOSE $PORT

# Start command (Railway will override with railway.json if present)
CMD ["/bin/bash", "-c", "source .venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port $PORT"]