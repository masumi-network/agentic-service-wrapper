# Masumi Agent

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

## Test

```bash
curl http://localhost:8000/availability
curl http://localhost:8000/input_schema
```
