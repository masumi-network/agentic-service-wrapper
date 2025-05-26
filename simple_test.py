#!/usr/bin/env python3
"""
Simple test script to call the Echo Agent directly
This bypasses the Masumi payment system for testing purposes
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_echo_agent(message: str):
    """Test the echo agent with a simple message"""
    print(f"🔊 Testing Echo Agent with message: '{message}'")
    print("=" * 50)
    
    # Step 1: Start a job
    print("📋 Step 1: Starting job...")
    job_data = {
        "input_data": [
            {"key": "text", "value": message}
        ]
    }
    
    response = requests.post(f"{BASE_URL}/start_job", json=job_data)
    if response.status_code != 200:
        print(f"❌ Failed to start job: {response.text}")
        return
    
    job_result = response.json()
    job_id = job_result["job_id"]
    print(f"✅ Job started with ID: {job_id}")
    
    # Step 2: Check job status
    print("\n📋 Step 2: Checking job status...")
    response = requests.get(f"{BASE_URL}/status?job_id={job_id}")
    if response.status_code != 200:
        print(f"❌ Failed to get status: {response.text}")
        return
    
    status_result = response.json()
    print(f"✅ Job status: {status_result['status']}")
    
    if status_result.get("result"):
        print(f"🎯 Result: {status_result['result']}")
    else:
        print("⏳ No result yet")
    
    print("\n🎉 Test completed successfully!")

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_test.py '<message>'")
        print("Example: python simple_test.py 'Hello, Echo Agent!'")
        return
    
    message = sys.argv[1]
    test_echo_agent(message)

if __name__ == "__main__":
    main() 