#!/usr/bin/env python3
"""
Simple Echo Agent for Masumi Network
Implements the Masumi Agentic Service API standard
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uvicorn

# Pydantic models for request/response validation
class InputData(BaseModel):
    key: str
    value: Any

class StartJobRequest(BaseModel):
    input_data: List[InputData]

class StartJobResponse(BaseModel):
    job_id: str
    payment_id: str

class StatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[str] = None

class AvailabilityResponse(BaseModel):
    status: str
    uptime: int
    message: str

class InputSchemaResponse(BaseModel):
    input_data: List[Dict[str, str]]

# In-memory job storage (in production, use a proper database)
jobs_db: Dict[str, Dict[str, Any]] = {}

# App startup time for uptime calculation
app_start_time = time.time()

# Create FastAPI app
app = FastAPI(
    title="Echo Agent Service",
    description="A simple echo agent that returns whatever you send to it",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint for basic health check"""
    return {
        "service": "Echo Agent",
        "version": "1.0.0",
        "description": "A simple echo agent for Masumi Network",
        "endpoints": ["/start_job", "/status", "/availability", "/input_schema"]
    }

@app.post("/start_job", response_model=StartJobResponse)
async def start_job(request: StartJobRequest):
    """
    Initiates a job on the echo service.
    The echo service simply stores the input and returns it as the result.
    """
    try:
        # Generate unique job and payment IDs
        job_id = str(uuid.uuid4())
        payment_id = str(uuid.uuid4())
        
        # Extract the input data
        input_text = ""
        for item in request.input_data:
            if item.key == "text":
                input_text = str(item.value)
                break
        
        if not input_text:
            # If no "text" key found, concatenate all values
            input_text = " ".join(str(item.value) for item in request.input_data)
        
        # Store job in our "database"
        jobs_db[job_id] = {
            "job_id": job_id,
            "payment_id": payment_id,
            "status": "awaiting_payment",
            "input_data": request.input_data,
            "input_text": input_text,
            "result": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"🚀 Job {job_id} created with input: {input_text}")
        
        return StartJobResponse(job_id=job_id, payment_id=payment_id)
        
    except Exception as e:
        print(f"❌ Error starting job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")

@app.get("/status", response_model=StatusResponse)
async def get_status(job_id: str = Query(..., description="The ID of the job to check")):
    """
    Retrieves the current status of a specific job.
    For the echo service, jobs automatically complete after being created.
    """
    try:
        if job_id not in jobs_db:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job = jobs_db[job_id]
        
        # Simulate job processing: if job is awaiting payment, mark as completed
        # In a real scenario, this would be triggered by payment confirmation
        if job["status"] == "awaiting_payment":
            # For demo purposes, auto-complete the job
            job["status"] = "completed"
            job["result"] = f"Echo: {job['input_text']}"
            job["updated_at"] = datetime.now().isoformat()
            
            print(f"✅ Job {job_id} completed with result: {job['result']}")
        
        return StatusResponse(
            job_id=job["job_id"],
            status=job["status"],
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
    Checks if the echo service is operational.
    """
    try:
        uptime_seconds = int(time.time() - app_start_time)
        
        return AvailabilityResponse(
            status="available",
            uptime=uptime_seconds,
            message="Echo service is running smoothly and ready to echo your messages!"
        )
        
    except Exception as e:
        print(f"❌ Error checking availability: {e}")
        raise HTTPException(status_code=500, detail=f"Service unavailable: {str(e)}")

@app.get("/input_schema", response_model=InputSchemaResponse)
async def get_input_schema():
    """
    Returns the expected input schema for the /start_job endpoint.
    The echo service expects a "text" field with the message to echo.
    """
    try:
        return InputSchemaResponse(
            input_data=[
                {"key": "text", "value": "string"}
            ]
        )
        
    except Exception as e:
        print(f"❌ Error getting input schema: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get input schema: {str(e)}")

# Additional endpoints for debugging and management
@app.get("/jobs")
async def list_jobs():
    """List all jobs (for debugging)"""
    return {"jobs": list(jobs_db.values())}

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job (for cleanup)"""
    if job_id in jobs_db:
        del jobs_db[job_id]
        return {"message": f"Job {job_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int(time.time() - app_start_time),
        "jobs_count": len(jobs_db)
    }

if __name__ == "__main__":
    print("🎯 Starting Echo Agent Service...")
    print("📋 Implementing Masumi Agentic Service API:")
    print("   - POST /start_job")
    print("   - GET /status")
    print("   - GET /availability") 
    print("   - GET /input_schema")
    print("🌐 Service will be available at http://localhost:8000")
    
    uvicorn.run(
        "echo_agent:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 