#!/usr/bin/env python3
"""
Test script for the Reverse Echo Agent with Masumi Payment Integration
This demonstrates the proper way to interact with the service
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_availability():
    """Test if the service is available"""
    print("🔍 Testing service availability...")
    response = requests.get(f"{BASE_URL}/availability")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Service is {data['status']}: {data['message']}")
        return True
    else:
        print(f"❌ Service not available: {response.status_code}")
        return False

def test_input_schema():
    """Test the input schema endpoint"""
    print("\n🔍 Testing input schema...")
    response = requests.get(f"{BASE_URL}/input_schema")
    if response.status_code == 200:
        data = response.json()
        print("✅ Input schema:")
        print(json.dumps(data, indent=2))
        return True
    else:
        print(f"❌ Failed to get input schema: {response.status_code}")
        return False

def test_direct_job():
    """Test the direct job endpoint (bypasses payment)"""
    print("\n🔍 Testing direct job (no payment)...")
    
    payload = {
        "identifier_from_purchaser": "test_user_123",
        "input_data": {
            "text": "Hello World"
        }
    }
    
    response = requests.post(f"{BASE_URL}/start_job_direct", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Direct job completed:")
        print(f"   Job ID: {data['job_id']}")
        print(f"   Status: {data['status']}")
        print(f"   Input: Hello World")
        print(f"   Result: {data['result']}")
        return data['job_id']
    else:
        print(f"❌ Direct job failed: {response.status_code} - {response.text}")
        return None

def test_payment_job():
    """Test the payment job endpoint (requires payment)"""
    print("\n🔍 Testing payment job (requires Masumi payment)...")
    
    payload = {
        "identifier_from_purchaser": "test_user_123",
        "input_data": {
            "text": "Masumi Network"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/start_job", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Payment job created:")
            print(f"   Job ID: {data['job_id']}")
            print(f"   Blockchain ID: {data['blockchainIdentifier']}")
            print(f"   Agent ID: {data['agentIdentifier']}")
            print(f"   Seller VKey: {data['sellerVkey']}")
            print(f"   Amount: {data['amounts']}")
            print(f"   Input: Masumi Network")
            return data['job_id']
        else:
            print(f"❌ Payment job failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Payment job error: {e}")
        return None

def test_job_status(job_id):
    """Test checking job status"""
    print(f"\n🔍 Testing job status for {job_id}...")
    
    response = requests.get(f"{BASE_URL}/status", params={"job_id": job_id})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Job status:")
        print(f"   Job ID: {data['job_id']}")
        print(f"   Status: {data['status']}")
        print(f"   Payment Status: {data.get('payment_status', 'N/A')}")
        print(f"   Result: {data.get('result', 'N/A')}")
        return data
    else:
        print(f"❌ Failed to get job status: {response.status_code}")
        return None

def test_configuration():
    """Test the configuration endpoint"""
    print("\n🔍 Testing configuration...")
    response = requests.get(f"{BASE_URL}/config")
    if response.status_code == 200:
        data = response.json()
        print("✅ Configuration:")
        for key, value in data.items():
            print(f"   {key}: {value}")
        return True
    else:
        print(f"❌ Failed to get configuration: {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("🎯 Testing Reverse Echo Agent with Masumi Payment Integration")
    print("=" * 60)
    
    # Test basic availability
    if not test_availability():
        print("❌ Service not available, stopping tests.")
        return
    
    # Test configuration
    test_configuration()
    
    # Test input schema
    test_input_schema()
    
    # Test direct job (no payment)
    direct_job_id = test_direct_job()
    if direct_job_id:
        test_job_status(direct_job_id)
    
    # Test payment job (will likely fail with placeholder agent ID)
    print("\n" + "="*60)
    print("⚠️  PAYMENT JOB TEST (Expected to fail with placeholder agent ID)")
    print("="*60)
    payment_job_id = test_payment_job()
    if payment_job_id:
        test_job_status(payment_job_id)
    else:
        print("💡 To make payment jobs work:")
        print("   1. Register your agent with Masumi Registry")
        print("   2. Update AGENT_IDENTIFIER in .env file")
        print("   3. Restart the service")
    
    print("\n🎉 Test suite completed!")

if __name__ == "__main__":
    main() 