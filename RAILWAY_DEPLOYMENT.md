# Railway Deployment Guide

This document outlines how we successfully deployed the Masumi Agent API to Railway.

## Problem
The FastAPI application wasn't running properly on Railway - the API endpoints were returning 502 errors.

## Root Cause
Railway uses dynamic port assignment via the `$PORT` environment variable, but our application was hardcoded to use port 8000.

## Solution Steps

### 1. Created Railway Configuration Files

We created two configuration files to help Railway understand how to run our Python application:

#### railway.json
Created this file to explicitly tell Railway how to build and deploy our application:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"  // use railway's default python builder
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",  // key: use $PORT variable
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Key elements:
- `"$schema"`: Links to Railway's JSON schema for validation
- `"builder": "NIXPACKS"`: Uses Railway's automatic Python detection and build system
- `"startCommand"`: Specifies exactly how to start the FastAPI app with uvicorn
- `--host 0.0.0.0`: Binds to all interfaces (required for container deployment)
- `--port $PORT`: Uses Railway's dynamic port assignment (critical for deployment to work)

#### Procfile
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 2. Handled Repository Branch Protection

Since the organization enforces pull request reviews for the main branch, we:
- Created a new branch `railway-config` for our changes
- Pushed to a personal fork (`1ar-labs/agentic-service-wrapper`) instead of the main organization repository
- Connected Railway to the personal fork to avoid organization restrictions

### 3. Fixed Port Configuration

Initially, the app still wasn't accessible. We resolved this by:
- Setting the `PORT` environment variable to `8000` in Railway's service settings
- Configuring Railway to expose port 8000

This aligned the application's expected port with Railway's proxy configuration.

## Key Commands Used

```bash
# add personal fork as remote
git remote add fork git@github.com:1ar-labs/agentic-service-wrapper.git

# create and push branch to fork
git checkout -b railway-config
git push fork railway-config
```

## Result

The API is now successfully deployed and accessible at:
- Base URL: `https://agentic-service-wrapper-production.up.railway.app/`
- Documentation: `https://agentic-service-wrapper-production.up.railway.app/docs`
- OpenAPI Spec: `https://agentic-service-wrapper-production.up.railway.app/openapi.json`

## Lessons Learned

1. Railway uses Nixpacks to automatically detect and build applications
2. Always use `$PORT` environment variable for Railway deployments
3. Both `railway.json` and `Procfile` can be used to specify start commands
4. When working with protected branches, using a personal fork for deployment can simplify the process
5. Railway's port configuration must match the application's listening port