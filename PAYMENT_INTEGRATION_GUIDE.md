# Masumi Payment Integration Guide

## Overview

This guide explains exactly where and how payment processing should be implemented in your Echo Agent to properly integrate with the Masumi Network.

## Current Status Analysis

### ✅ What You Have:
- Echo Agent registered on Masumi Network (Agent ID 320)
- Echo Agent service running on localhost:8000
- Masumi Payment Service running on localhost:3001
- Basic agent API endpoints (`/start_job`, `/status`, `/availability`)

### ❌ What Was Missing:
- **Payment integration inside your agent service**
- Communication between agent and payment service
- Proper payment verification before job completion

## Where Payment Should Be Handled

According to Masumi documentation, payment processing must happen **inside your agent service**, not as external scripts. Your agent needs to:

1. **Create payment requests** when jobs are started
2. **Check payment status** before processing jobs
3. **Update payment completion** after jobs finish

## Implementation Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │    │   Echo Agent     │    │ Payment Service │
│                 │    │  (localhost:8000)│    │ (localhost:3001)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │ 1. POST /start_job    │                       │
         ├──────────────────────►│                       │
         │                       │ 2. Create payment     │
         │                       ├──────────────────────►│
         │                       │ 3. Return payment_id  │
         │                       │◄──────────────────────┤
         │ 4. job_id+payment_id  │                       │
         │◄──────────────────────┤                       │
         │                       │                       │
         │ 5. Make payment       │                       │
         ├───────────────────────┼──────────────────────►│
         │                       │                       │
         │ 6. GET /status        │                       │
         ├──────────────────────►│                       │
         │                       │ 7. Check payment     │
         │                       ├──────────────────────►│
         │                       │ 8. Payment confirmed  │
         │                       │◄──────────────────────┤
         │                       │ 9. Process job        │
         │                       │                       │
         │ 10. Return result     │                       │
         │◄──────────────────────┤                       │
```

## Required Changes to Your Agent

### 1. **Enhanced `/start_job` Endpoint**

**Before (your current implementation):**
```python
@app.post("/start_job")
async def start_job(request: StartJobRequest):
    job_id = str(uuid.uuid4())
    payment_id = str(uuid.uuid4())  # Just generates random ID
    
    # Stores job without payment integration
    jobs_db[job_id] = {
        "job_id": job_id,
        "payment_id": payment_id,
        "status": "awaiting_payment"
    }
    
    return {"job_id": job_id, "payment_id": payment_id}
```

**After (payment-integrated):**
```python
@app.post("/start_job")
async def start_job(request: StartJobRequest):
    job_id = str(uuid.uuid4())
    
    # Create actual payment request with Masumi Payment Service
    payment_id = create_payment_request(job_id, AGENT_PRICE_LOVELACE)
    
    if not payment_id:
        raise HTTPException(status_code=500, detail="Failed to create payment request")
    
    jobs_db[job_id] = {
        "job_id": job_id,
        "payment_id": payment_id,  # Real payment ID from service
        "status": "awaiting_payment",
        "payment_status": "pending"
    }
    
    return {"job_id": job_id, "payment_id": payment_id}
```

### 2. **Enhanced `/status` Endpoint**

**Before (auto-completes without payment):**
```python
@app.get("/status")
async def get_status(job_id: str):
    job = jobs_db[job_id]
    
    # Auto-completes without checking payment!
    if job["status"] == "awaiting_payment":
        job["status"] = "completed"
        job["result"] = f"Echo: {job['input_text']}"
    
    return job
```

**After (checks payment before processing):**
```python
@app.get("/status")
async def get_status(job_id: str):
    job = jobs_db[job_id]
    payment_id = job["payment_id"]
    
    # Check payment status if job is still awaiting payment
    if job["status"] == "awaiting_payment":
        payment_status = check_payment_status(payment_id)
        job["payment_status"] = payment_status
        
        # Only process if payment is confirmed
        if payment_status == "completed":
            job["status"] = "completed"
            job["result"] = f"Echo: {job['input_text']}"
            
            # Update payment completion on blockchain
            update_payment_completion(payment_id, job_id)
    
    return job
```

## Required Payment Service Integration Functions

Your agent needs these three functions to communicate with the Payment Service:

### 1. **Create Payment Request**
```python
def create_payment_request(job_id: str, amount: int) -> Optional[str]:
    """Creates payment request with Masumi Payment Service"""
    url = f"{MASUMI_PAYMENT_BASE_URL}/payments"
    payload = {
        "identifier": job_id,
        "amount": amount,
        "currency": "ADA"
    }
    # Returns actual payment_id from service
```

### 2. **Check Payment Status**
```python
def check_payment_status(payment_id: str) -> str:
    """Checks if payment has been confirmed on blockchain"""
    url = f"{MASUMI_PAYMENT_BASE_URL}/payments/{payment_id}"
    # Returns: 'pending', 'completed', 'failed'
```

### 3. **Update Payment Completion**
```python
def update_payment_completion(payment_id: str, job_id: str) -> bool:
    """Updates payment status after job completion"""
    url = f"{MASUMI_PAYMENT_BASE_URL}/payments/{payment_id}"
    payload = {"status": "completed", "job_id": job_id}
    # Updates blockchain record
```

## Files Created

### 1. **`echo_agent_with_payments.py`**
- Complete payment-integrated version of your echo agent
- Implements all required Masumi payment flow steps
- Ready to replace your current `echo_agent.py`

### 2. **`test_payment_integration.py`**
- Test script to verify payment integration works
- Tests the complete flow: job creation → payment → completion
- Helps debug payment issues

## How to Test the Integration

### Step 1: Stop Current Agent
```bash
# Stop your current echo_agent.py if running
# Ctrl+C in the terminal where it's running
```

### Step 2: Start Payment-Integrated Agent
```bash
cd agentic-service
python echo_agent_with_payments.py
```

### Step 3: Test the Integration
```bash
# In another terminal
python test_payment_integration.py 'Hello payment integration!'
```

## Expected Flow

### 1. **Job Creation with Payment**
```
🚀 Starting job with message: 'Hello payment integration!'
✅ Job started successfully!
🆔 Job ID: abc123...
💳 Payment ID: def456...
📊 Status: awaiting_payment
```

### 2. **Payment Processing**
```
💳 Making payment for job abc123...
💼 Found seller wallet: addr_test1q...
✅ Payment submitted successfully!
```

### 3. **Job Completion After Payment**
```
📊 Job Status: completed
💰 Payment Status: completed
🎯 Result: Echo: Hello payment integration!
```

## Key Differences from Your Current Setup

| Aspect | Current (No Payment) | Payment-Integrated |
|--------|---------------------|-------------------|
| **Payment ID** | Random UUID | Real payment from service |
| **Job Processing** | Auto-completes | Waits for payment confirmation |
| **Status Checks** | Always returns result | Checks payment first |
| **Blockchain Integration** | None | Updates payment status on-chain |
| **Error Handling** | Basic | Payment failure handling |

## Common Issues and Solutions

### 1. **Payment Service Not Reachable**
```
❌ Error creating payment request: Connection refused
```
**Solution:** Ensure Masumi Payment Service is running on port 3001

### 2. **No Seller Wallet Found**
```
❌ No Preprod seller wallet found in payment service
```
**Solution:** Check wallet configuration in payment service admin interface

### 3. **Payment Endpoint Errors**
```
❌ Payment service error: 404 - Not Found
```
**Solution:** Verify payment service API endpoints and authentication

## Production Considerations

### 1. **Database Storage**
- Replace in-memory `jobs_db` with persistent database
- Store payment status and job results permanently

### 2. **Error Handling**
- Implement retry logic for payment service calls
- Handle network timeouts gracefully
- Add proper logging for payment events

### 3. **Security**
- Use environment variables for payment service credentials
- Implement proper authentication for agent endpoints
- Validate payment amounts and currencies

### 4. **Monitoring**
- Add metrics for payment success/failure rates
- Monitor payment processing times
- Alert on payment service connectivity issues

## Next Steps

1. **Test the payment-integrated agent** using the provided scripts
2. **Verify payment flow** works end-to-end
3. **Update your registration** if needed to point to the new agent
4. **Monitor payment processing** in production
5. **Implement additional features** like refunds, partial payments, etc.

## Summary

The key insight is that **payment processing must be embedded inside your agent service**, not handled externally. Your agent becomes the orchestrator that:

- Creates payment requests when jobs start
- Verifies payments before processing
- Updates payment status after completion

This ensures proper integration with the Masumi Network's payment infrastructure and blockchain verification system. 