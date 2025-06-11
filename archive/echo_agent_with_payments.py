#!/usr/bin/env python3
"""
Echo Agent with Masumi Payment Integration
Implements proper payment flow using the official Masumi SDK
"""

import time
import uuid
import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Masumi SDK
try:
    from masumi.config import Config
    from masumi.payment import Payment, Amount
    MASUMI_SDK_AVAILABLE = True
except ImportError:
    print("⚠️  Masumi SDK not installed. Run: pip install masumi")
    MASUMI_SDK_AVAILABLE = False

# Configuration from environment variables
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:3001/api/v1")
PAYMENT_API_KEY = os.getenv("PAYMENT_API_KEY", "myadminkeyisalsoverysafe")
AGENT_IDENTIFIER = os.getenv("AGENT_IDENTIFIER", "your_agent_identifier_here")
PAYMENT_AMOUNT = os.getenv("PAYMENT_AMOUNT", "10000000")
PAYMENT_UNIT = os.getenv("PAYMENT_UNIT", "lovelace")
SELLER_VKEY = os.getenv("SELLER_VKEY", "your_seller_vkey_here")
NETWORK = os.getenv("NETWORK", "Preprod")

# Pydantic models for request/response validation (MIP-003 compliant)
class InputData(BaseModel):
    key: str
    value: Any

class StartJobRequest(BaseModel):
    identifier_from_purchaser: str = Field(
        ...,
        description="Unique identifier for the purchaser/client making the request",
        example="user_12345"
    )
    input_data: Dict[str, Any] = Field(
        ...,
        description="Input data containing the text to be reversed",
        example={"text": "Hello Masumi Network!"}
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "identifier_from_purchaser": "user_12345",
                "input_data": {
                    "text": "Hello Masumi Network!"
                }
            }
        }
    }

class StartJobResponse(BaseModel):
    status: str = Field(default="success", description="Status of the job creation")
    job_id: str = Field(..., description="Unique identifier for the created job")
    blockchainIdentifier: str = Field(..., description="Blockchain identifier for payment tracking")
    submitResultTime: str = Field(..., description="Deadline for submitting results")
    unlockTime: str = Field(..., description="Time when funds unlock if no result submitted")
    externalDisputeUnlockTime: str = Field(..., description="Time when external dispute resolution becomes available")
    agentIdentifier: str = Field(..., description="Unique identifier of the agent")
    sellerVkey: str = Field(..., description="Seller's verification key")
    identifierFromPurchaser: str = Field(..., description="Echo of the purchaser identifier")
    amounts: List[Dict[str, str]] = Field(..., description="Payment amounts required")
    input_hash: Optional[str] = Field(None, description="Hash of the input data")

class StatusResponse(BaseModel):
    job_id: str = Field(..., description="Unique identifier of the job")
    status: str = Field(..., description="Current status of the job", example="completed")
    payment_status: Optional[str] = Field(None, description="Status of the payment", example="completed")
    result: Optional[str] = Field(None, description="Result of the job execution", example="Reversed: !krowteN imusamM olleH")

class AvailabilityResponse(BaseModel):
    status: str = Field(..., description="Service availability status", example="available")
    type: str = Field(default="masumi-agent", description="Type of service")
    message: str = Field(..., description="Human-readable status message", example="Server operational.")

class InputSchemaItem(BaseModel):
    id: str = Field(..., description="Identifier for the input field", example="text")
    type: str = Field(..., description="Data type of the input", example="string")
    name: str = Field(..., description="Human-readable name for the input", example="Text to Reverse")
    data: Dict[str, str] = Field(..., description="Additional metadata about the input field")

class InputSchemaResponse(BaseModel):
    input_data: List[InputSchemaItem] = Field(..., description="List of input schema items")

class ProvideInputRequest(BaseModel):
    job_id: str = Field(..., description="ID of the job to provide input for", example="550e8400-e29b-41d4-a716-446655440000")
    input_data: List[Dict[str, Any]] = Field(
        ...,
        description="Additional input data for the job",
        example=[{"text": "Additional text to process"}]
    )

# In-memory job storage (in production, use a proper database)
jobs_db: Dict[str, Dict[str, Any]] = {}
payment_instances: Dict[str, Any] = {}

# App startup time for uptime calculation
app_start_time = time.time()

# Initialize Masumi Config
if MASUMI_SDK_AVAILABLE:
    config = Config(
        payment_service_url=PAYMENT_SERVICE_URL,
        payment_api_key=PAYMENT_API_KEY
    )
else:
    config = None

# Create FastAPI app
app = FastAPI(
    title="Reverse Echo Agent Service with Masumi Payment Integration",
    description="Reverse echo agent that returns input text reversed, integrated with official Masumi Payment SDK",
    version="1.0.0"
)

async def execute_echo_task(input_data: Dict[str, Any]) -> str:
    """Execute the reverse echo task - return the input string reversed"""
    # Extract text from input_data
    if isinstance(input_data, dict):
        text = input_data.get("text", "")
        if not text:
            # If no "text" key, concatenate all values
            text = " ".join(str(v) for v in input_data.values())
    else:
        text = str(input_data)
    
    # Simulate some processing time
    await asyncio.sleep(0.1)
    
    # Reverse the text and return it
    reversed_text = text[::-1]
    return f"Reversed: {reversed_text}"

async def handle_payment_status(job_id: str, payment_id: str) -> None:
    """Executes echo task after payment confirmation"""
    try:
        print(f"💰 Payment {payment_id} completed for job {job_id}, executing task...")
        
        # Update job status to running
        jobs_db[job_id]["status"] = "running"
        input_data = jobs_db[job_id]["input_data"]
        
        # Execute the echo task
        result = await execute_echo_task(input_data)
        print(f"✅ Echo task completed for job {job_id}: {result}")
        
        # Mark payment as completed on Masumi
        if job_id in payment_instances:
            await payment_instances[job_id].complete_payment(payment_id, {"result": result})
            print(f"💳 Payment completed for job {job_id}")
        
        # Update job status
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["payment_status"] = "completed"
        jobs_db[job_id]["result"] = result
        jobs_db[job_id]["updated_at"] = datetime.now().isoformat()
        
        # Stop monitoring payment status
        if job_id in payment_instances:
            payment_instances[job_id].stop_status_monitoring()
            del payment_instances[job_id]
            
    except Exception as e:
        print(f"❌ Error processing payment {payment_id} for job {job_id}: {e}")
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)
        
        # Still stop monitoring to prevent repeated failures
        if job_id in payment_instances:
            payment_instances[job_id].stop_status_monitoring()
            del payment_instances[job_id]

@app.get("/")
async def root():
    """Root endpoint for basic health check"""
    return {
        "service": "Reverse Echo Agent with Masumi Payment Integration",
        "version": "1.0.0",
        "description": "Reverse echo agent that returns input text reversed using official Masumi SDK",
        "endpoints": ["/start_job", "/status", "/availability", "/input_schema"],
        "payment_integration": MASUMI_SDK_AVAILABLE,
        "payment_service_url": PAYMENT_SERVICE_URL
    }

@app.post("/start_job", response_model=StartJobResponse)
async def start_job(
    request: StartJobRequest = Body(
        ...,
        example={
            "identifier_from_purchaser": "buyer_456",
            "input_data": {
                "text": "Masumi Network rocks!"
            }
        }
    )
):
    """
    **Start a paid job that reverses input text**
    
    Creates a new job that requires payment via the Masumi Network.
    The job will reverse the provided text and return it once payment is confirmed.
    
    - **identifier_from_purchaser**: Your unique identifier as the purchaser
    - **input_data**: Object containing the text to be reversed (key: "text")
    
    **Example Input:**
    ```json
    {
        "identifier_from_purchaser": "buyer_456",
        "input_data": {"text": "Masumi Network rocks!"}
    }
    ```
    
    Returns payment information including blockchain identifier for tracking.
    Use the `/status` endpoint with the returned `job_id` to check progress and get results.
    """
    if not MASUMI_SDK_AVAILABLE:
        raise HTTPException(status_code=500, detail="Masumi SDK not available. Install with: pip install masumi")
    
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        print(f"🚀 Starting job {job_id} with Masumi payment integration")
        print(f"📝 Input data: {request.input_data}")
        print(f"👤 Purchaser ID: {request.identifier_from_purchaser}")
        
        # Define payment amounts
        amounts = [Amount(amount=PAYMENT_AMOUNT, unit=PAYMENT_UNIT)]
        print(f"💰 Payment amount: {PAYMENT_AMOUNT} {PAYMENT_UNIT}")
        
        # Create a payment request using Masumi SDK
        payment = Payment(
            agent_identifier=AGENT_IDENTIFIER,
            amounts=amounts,
            config=config,
            identifier_from_purchaser=request.identifier_from_purchaser,
            input_data=request.input_data,
            network=NETWORK
        )
        
        print("💳 Creating payment request...")
        payment_request = await payment.create_payment_request()
        payment_id = payment_request["data"]["blockchainIdentifier"]
        payment.payment_ids.add(payment_id)
        print(f"✅ Created payment request with ID: {payment_id}")
        
        # Store job in our "database"
        jobs_db[job_id] = {
            "job_id": job_id,
            "payment_id": payment_id,
            "status": "awaiting_payment",
            "payment_status": "pending",
            "input_data": request.input_data,
            "result": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "identifier_from_purchaser": request.identifier_from_purchaser
        }
        
        # Define payment callback
        async def payment_callback(payment_id: str):
            await handle_payment_status(job_id, payment_id)
        
        # Start monitoring the payment status
        payment_instances[job_id] = payment
        print(f"👀 Starting payment status monitoring for job {job_id}")
        await payment.start_status_monitoring(payment_callback)
        
        # Return MIP-003 compliant response
        return StartJobResponse(
            status="success",
            job_id=job_id,
            blockchainIdentifier=payment_request["data"]["blockchainIdentifier"],
            submitResultTime=payment_request["data"]["submitResultTime"],
            unlockTime=payment_request["data"]["unlockTime"],
            externalDisputeUnlockTime=payment_request["data"]["externalDisputeUnlockTime"],
            agentIdentifier=AGENT_IDENTIFIER,
            sellerVkey=SELLER_VKEY,
            identifierFromPurchaser=request.identifier_from_purchaser,
            amounts=[{"amount": PAYMENT_AMOUNT, "unit": PAYMENT_UNIT}],
            input_hash=getattr(payment, 'input_hash', None)
        )
        
    except Exception as e:
        print(f"❌ Error starting job: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")

@app.post("/start_job_direct", 
          responses={
              200: {
                  "description": "Job completed successfully",
                  "content": {
                      "application/json": {
                          "example": {
                              "job_id": "82acdf56-91f1-4631-8540-6d50492bd48d",
                              "status": "completed",
                              "result": "Reversed: !krowteN imusaM olleH",
                              "message": "Job completed without payment (direct access)"
                          }
                      }
                  }
              }
          })
async def start_job_direct(
    request: StartJobRequest = Body(
        ...,
        example={
            "identifier_from_purchaser": "test_user_123",
            "input_data": {
                "text": "Hello Masumi Network!"
            }
        }
    )
):
    """
    **Start a job without payment (testing/demo)**
    
    Immediately processes and reverses the input text without requiring payment.
    Perfect for testing the reverse text functionality.
    
    - **identifier_from_purchaser**: Your unique identifier as the purchaser
    - **input_data**: Object containing the text to be reversed (key: "text")
    
    **Example Input:**
    ```json
    {
        "identifier_from_purchaser": "test_user_123",
        "input_data": {"text": "Hello World"}
    }
    ```
    
    **Example Output:**
    ```json
    {
        "job_id": "uuid-here",
        "status": "completed", 
        "result": "Reversed: dlroW olleH",
        "message": "Job completed without payment (direct access)"
    }
    ```
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        print(f"🚀 Starting direct job {job_id} (bypassing payment)")
        
        # Process immediately without payment
        result = await execute_echo_task(request.input_data)
        
        # Store completed job in our "database"
        jobs_db[job_id] = {
            "job_id": job_id,
            "payment_id": None,
            "status": "completed",
            "payment_status": "bypassed",
            "input_data": request.input_data,
            "result": result,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "identifier_from_purchaser": request.identifier_from_purchaser
        }
        
        print(f"✅ Direct job {job_id} completed: {result}")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "result": result,
            "message": "Job completed without payment (direct access)"
        }
        
    except Exception as e:
        print(f"❌ Error starting direct job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start direct job: {str(e)}")

@app.get("/status", response_model=StatusResponse)
async def get_status(job_id: str = Query(..., description="The unique ID of the job to check", example="550e8400-e29b-41d4-a716-446655440000")):
    """
    **Check job status and get results**
    
    Retrieves the current status of a specific job and its results if completed.
    
    - **job_id**: The unique identifier returned when the job was created
    
    Possible statuses:
    - `awaiting_payment`: Job created, waiting for payment
    - `processing`: Payment confirmed, job is running
    - `completed`: Job finished, result available
    - `failed`: Job failed due to error
    """
    try:
        if job_id not in jobs_db:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job = jobs_db[job_id]
        
        # For jobs with payment monitoring, the status is updated automatically
        # via the payment callback, so we just return the current status
        
        return StatusResponse(
            job_id=job["job_id"],
            status=job["status"],
            payment_status=job.get("payment_status"),
            result=job["result"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting status for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@app.get("/availability", response_model=AvailabilityResponse)
async def check_availability():
    """
    **Check if the service is operational**
    
    Simple health check to verify the reverse echo agent is running and ready to accept jobs.
    """
    try:
        return AvailabilityResponse(
            status="available",
            type="masumi-agent",
            message="Server operational."
        )
        
    except Exception as e:
        print(f"❌ Error checking availability: {e}")
        raise HTTPException(status_code=500, detail=f"Service unavailable: {str(e)}")

@app.get("/input_schema", response_model=InputSchemaResponse)
async def get_input_schema():
    """
    **Get input requirements for jobs**
    
    Returns the expected input format for starting jobs.
    This endpoint tells you what data structure to send in the `input_data` field.
    
    Currently expects:
    - **text**: String to be reversed by the agent
    """
    try:
        return InputSchemaResponse(
            input_data=[
                InputSchemaItem(
                    id="text",
                    type="string",
                    name="Text to Reverse",
                    data={
                        "description": "The text input that will be reversed by the agent",
                        "placeholder": "Enter your text to reverse here"
                    }
                )
            ]
        )
        
    except Exception as e:
        print(f"❌ Error getting input schema: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get input schema: {str(e)}")

@app.post("/provide_input")
async def provide_input(request: ProvideInputRequest):
    """
    Provides additional input to an existing job.
    MIP-003 compliant implementation.
    """
    try:
        job_id = request.job_id
        
        if job_id not in jobs_db:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs_db[job_id]
        
        # Only allow additional input for jobs that are in progress
        if job["status"] not in ["processing", "awaiting_input"]:
            raise HTTPException(status_code=400, detail="Job is not in a state that accepts additional input")
        
        # Store the additional input
        if "additional_inputs" not in job:
            job["additional_inputs"] = []
        
        job["additional_inputs"].append({
            "timestamp": datetime.now().isoformat(),
            "input_data": request.input_data
        })
        
        job["updated_at"] = datetime.now().isoformat()
        
        print(f"📝 Additional input provided for job {job_id}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error providing input for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to provide input: {str(e)}")

# Additional endpoints for debugging and management
@app.get("/jobs")
async def list_jobs():
    """List all jobs (for debugging)"""
    return {"jobs": list(jobs_db.values())}

@app.get("/payments")
async def list_payments():
    """List payment status for all jobs (for debugging)"""
    payments = []
    for job in jobs_db.values():
        payments.append({
            "job_id": job["job_id"],
            "payment_id": job.get("payment_id"),
            "status": job["status"],
            "payment_status": job.get("payment_status", "unknown")
        })
    return {"payments": payments}

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job (for cleanup)"""
    if job_id in jobs_db:
        # Stop payment monitoring if it exists
        if job_id in payment_instances:
            payment_instances[job_id].stop_status_monitoring()
            del payment_instances[job_id]
        
        del jobs_db[job_id]
        return {"message": f"Job {job_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

@app.get("/health")
async def health_check():
    """Simple health check endpoint - returns plain text OK"""
    return "OK"

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check endpoint with full status information"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int(time.time() - app_start_time),
        "jobs_count": len(jobs_db),
        "payment_service_url": PAYMENT_SERVICE_URL,
        "masumi_sdk_available": MASUMI_SDK_AVAILABLE,
        "agent_identifier": AGENT_IDENTIFIER,
        "network": NETWORK
    }

@app.get("/config")
async def get_config():
    """Get current configuration (for debugging)"""
    return {
        "payment_service_url": PAYMENT_SERVICE_URL,
        "agent_identifier": AGENT_IDENTIFIER,
        "payment_amount": PAYMENT_AMOUNT,
        "payment_unit": PAYMENT_UNIT,
        "seller_vkey": SELLER_VKEY,
        "network": NETWORK,
        "masumi_sdk_available": MASUMI_SDK_AVAILABLE
    }

if __name__ == "__main__":
    print("🎯 Starting Reverse Echo Agent Service with Masumi Payment Integration...")
    print("📋 Using Official Masumi SDK")
    print("   - POST /start_job (with Masumi payment)")
    print("   - POST /start_job_direct (bypass payment)")
    print("   - GET /status")
    print("   - GET /availability") 
    print("   - GET /input_schema")
    print("   - POST /provide_input")
    print(f"💳 Payment Service: {PAYMENT_SERVICE_URL}")
    print(f"🔑 Agent ID: {AGENT_IDENTIFIER}")
    print(f"💰 Price: {PAYMENT_AMOUNT} {PAYMENT_UNIT}")
    print(f"🌐 Network: {NETWORK}")
    print(f"📦 Masumi SDK Available: {MASUMI_SDK_AVAILABLE}")
    print(f"🔄 Function: Reverses input text")
    
    if not MASUMI_SDK_AVAILABLE:
        print("⚠️  Install Masumi SDK with: pip install masumi")
    
    print("🌐 Service will be available at http://localhost:8000")
    
    uvicorn.run(
        "echo_agent_with_payments:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 