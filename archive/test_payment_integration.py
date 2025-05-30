#!/usr/bin/env python3
"""
Test script for Echo Agent with Payment Integration
Tests the full payment flow according to Masumi documentation
"""

import requests
import time
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
ECHO_AGENT_URL = "http://localhost:8000"
MASUMI_PAYMENT_URL = "http://localhost:3001/api/v1"
MASUMI_PAYMENT_TOKEN = os.getenv("MASUMI_PAYMENT_TOKEN")

def test_agent_availability():
    """Test if the echo agent is running"""
    try:
        response = requests.get(f"{ECHO_AGENT_URL}/availability", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Echo Agent is available: {data['message']}")
            return True
        else:
            print(f"❌ Echo Agent not available: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach Echo Agent: {e}")
        return False

def test_payment_service():
    """Test if the payment service is running"""
    try:
        response = requests.get(f"{MASUMI_PAYMENT_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Payment Service is available")
            return True
        else:
            print(f"❌ Payment Service not available: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach Payment Service: {e}")
        return False

def start_job_with_payment(message: str):
    """Start a job that requires payment"""
    url = f"{ECHO_AGENT_URL}/start_job"
    payload = {
        "input_data": [
            {"key": "text", "value": message}
        ]
    }
    
    print(f"\n🚀 Starting job with message: '{message}'")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Job started successfully!")
        print(f"🆔 Job ID: {data['job_id']}")
        print(f"🔗 Blockchain ID: {data['blockchainIdentifier']}")
        print(f"📊 Status: {data.get('status', 'awaiting_payment')}")
        print(f"💰 Amount: {data['amounts'][0]['amount']} {data['amounts'][0]['unit']}")
        print(f"🏦 Seller: {data['sellerWalletAddress']}")
        
        return data['job_id'], data['blockchainIdentifier']
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error starting job: {e}")
        return None, None

def check_job_status(job_id: str):
    """Check the status of a job"""
    url = f"{ECHO_AGENT_URL}/status?job_id={job_id}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"📊 Job Status: {data['status']}")
        if data.get('payment_status'):
            print(f"💰 Payment Status: {data['payment_status']}")
        if data.get('result'):
            print(f"🎯 Result: {data['result']}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking job status: {e}")
        return None

def make_payment_via_masumi(job_id: str, blockchain_id: str):
    """Check if payment was created and provide instructions"""
    print(f"💳 Checking payment for job {job_id}...")
    print(f"🔗 Blockchain ID: {blockchain_id}")
    
    # Check if the purchase was created
    url = f"{MASUMI_PAYMENT_URL}/purchase/"
    headers = {
        "token": MASUMI_PAYMENT_TOKEN
    }
    params = {
        "network": "Preprod",
        "limit": 50
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                purchases = data.get("data", {}).get("Purchases", [])
                
                for purchase in purchases:
                    if purchase.get("blockchainIdentifier") == blockchain_id:
                        print(f"✅ Purchase found in payment service!")
                        print(f"📊 State: {purchase.get('onChainState', 'Unknown')}")
                        print(f"💰 Amount: {purchase.get('amount', 'Unknown')} lovelace")
                        
                        # In a real client, you would now make the actual blockchain payment
                        print("\n💡 Next steps for real payment:")
                        print("1. Client wallet would create a transaction")
                        print("2. Send funds to the smart contract")
                        print("3. Payment service would detect the transaction")
                        print("4. Agent would be notified and process the job")
                        
                        return True
                
                print(f"❌ No purchase found with blockchain ID {blockchain_id}")
                return False
            else:
                print(f"❌ Error checking purchases: {data}")
                return False
        else:
            print(f"❌ Payment service error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking payment: {e}")
        return False

def wait_for_job_completion(job_id: str, max_wait_time: int = 120):
    """Wait for job to complete and return final result"""
    print(f"\n⏳ Waiting for job {job_id} to complete (max {max_wait_time}s)...")
    
    start_time = time.time()
    check_interval = 10  # Check every 10 seconds
    
    while time.time() - start_time < max_wait_time:
        status_data = check_job_status(job_id)
        
        if status_data:
            status = status_data.get("status", "").lower()
            
            if status == "completed":
                print("🎉 Job completed successfully!")
                return status_data
            elif status == "failed":
                print(f"💥 Job failed: {status_data}")
                return status_data
            elif status in ["awaiting_payment", "processing"]:
                print(f"⏳ Job status: {status}")
            else:
                print(f"🤔 Unknown status: {status}")
        
        print(f"💤 Waiting {check_interval}s before next check...")
        time.sleep(check_interval)
    
    print(f"⏰ Timeout after {max_wait_time}s")
    return None

def main():
    """Main test function"""
    if len(sys.argv) < 2:
        message = "Hello, testing payment integration!"
    else:
        message = sys.argv[1]
    
    print("🧪 Testing Echo Agent with Payment Integration")
    print("=" * 60)
    
    # Step 1: Test services availability
    print("\n📋 Step 1: Testing Service Availability...")
    if not test_agent_availability():
        print("💡 Please start the payment-integrated echo agent:")
        print("   python echo_agent_with_payments.py")
        return
    
    if not test_payment_service():
        print("💡 Please ensure the Masumi Payment Service is running on port 3001")
        return
    
    # Step 2: Start job with payment
    print("\n📋 Step 2: Starting Job with Payment...")
    job_id, blockchain_id = start_job_with_payment(message)
    if not job_id:
        print("❌ Failed to start job")
        return
    
    # Step 3: Check initial status (should be awaiting payment)
    print("\n📋 Step 3: Checking Initial Status...")
    initial_status = check_job_status(job_id)
    if not initial_status:
        print("❌ Failed to check job status")
        return
    
    # Step 4: Make payment
    print("\n📋 Step 4: Making Payment...")
    payment_success = make_payment_via_masumi(job_id, blockchain_id)
    if not payment_success:
        print("❌ Payment failed")
        print("💡 Common reasons:")
        print("   - Insufficient funds in purchasing wallet")
        print("   - Payment service configuration issues")
        return
    
    # Step 5: Wait for completion
    print("\n📋 Step 5: Waiting for Job Completion...")
    final_result = wait_for_job_completion(job_id)
    
    if final_result:
        print("\n🎯 Final Result:")
        print("=" * 50)
        result = final_result.get("result")
        if result:
            print(f"🔊 Echo Response: {result}")
        else:
            print(json.dumps(final_result, indent=2))
        
        print("\n🎉 Payment Integration Test Completed Successfully!")
        print("✅ Your Echo Agent now properly integrates with Masumi Payment Service")
    else:
        print("\n❌ Test failed - no final result obtained")

if __name__ == "__main__":
    main() 