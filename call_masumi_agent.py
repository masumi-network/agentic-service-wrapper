#!/usr/bin/env python3
"""
Script to call Masumi Agent 118 - Patrick's Research Summary Agent
This version includes Registry Service discovery and better error handling
"""

import requests
import time
import json
import sys
from typing import Dict, Any, Optional

# Configuration from your environment
MASUMI_PAYMENT_BASE_URL = "http://localhost:3001/api/v1"
MASUMI_PAYMENT_TOKEN = "myadminkeyisalsoverysafe"  # Your admin key

    # Echo Agent 320 information (your registered agent)
AGENT_ID = "320"
FALLBACK_AGENT_API_BASE_URL = "http://localhost:8000"
FALLBACK_AGENT_PRICE_LOVELACE = 10000  # 0.01 tADA
AGENT_PRICE_CURRENCY = "ADA"


def get_agent_info_from_registry(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Try to get agent information from Registry Service
    """
    # Common registry service URLs to try
    registry_urls = [
        "http://localhost:3000",  # Local registry
        "https://registry.masumi.network",  # Official registry
        "https://api.masumi.network"  # API endpoint
    ]
    
    for base_url in registry_urls:
        try:
            # Try different possible endpoints
            endpoints = [
                f"/payment-information/{agent_id}",
                f"/registry/payment-information/{agent_id}",
                f"/api/v1/payment-information/{agent_id}",
                f"/agents/{agent_id}/payment-information"
            ]
            
            for endpoint in endpoints:
                url = f"{base_url}{endpoint}"
                print(f"🔍 Trying registry: {url}")
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Got registry data: {json.dumps(data, indent=2)}")
                    return data
                else:
                    print(f"❌ {response.status_code}: {response.text[:100]}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ Registry check failed for {base_url}: {e}")
            continue
    
    print("🤷 No registry service found, using fallback values")
    return None


def get_wallet_from_payment_service() -> Optional[str]:
    """
    Get the seller wallet address from our payment service configuration
    """
    url = f"{MASUMI_PAYMENT_BASE_URL}/payment-source/"
    headers = {
        "accept": "application/json",
        "token": MASUMI_PAYMENT_TOKEN
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") == "success":
            payment_sources = data.get("data", {}).get("PaymentSources", [])
            for source in payment_sources:
                if source.get("network") == "Preprod":
                    selling_wallets = source.get("SellingWallets", [])
                    if selling_wallets:
                        wallet_addr = selling_wallets[0].get("walletAddress")
                        print(f"📍 Found seller wallet: {wallet_addr}")
                        return wallet_addr
        
        print("❌ No Preprod seller wallet found in payment service")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting wallet from payment service: {e}")
        return None


def test_agent_endpoint(base_url: str) -> bool:
    """
    Test if the agent endpoint is reachable
    """
    test_urls = [
        f"{base_url}/health",
        f"{base_url}/status",
        f"{base_url}/",
        f"{base_url}/docs"
    ]
    
    for url in test_urls:
        try:
            print(f"🩺 Testing: {url}")
            response = requests.get(url, timeout=10)
            if response.status_code in [200, 404]:  # 404 is fine, means server is up
                print(f"✅ Agent service is reachable at {base_url}")
                return True
        except requests.exceptions.RequestException:
            continue
    
    print(f"❌ Agent service not reachable at {base_url}")
    return False


def start_agent_job(base_url: str, topic: str) -> Optional[str]:
    """
    Start a job with Echo Agent 320
    """
    url = f"{base_url.rstrip('/')}/start_job"
    
    # Based on the echo agent's input schema
    payload = {
        "input_data": [
            {"key": "text", "value": topic}
        ]
    }
    
    print(f"🚀 Starting job with Agent 118...")
    print(f"📍 URL: {url}")
    print(f"📝 Topic: {topic}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Job started successfully!")
        print(f"📄 Response: {json.dumps(data, indent=2)}")
        
        # Extract job_id - this might be in different keys depending on the agent
        job_id = data.get("job_id") or data.get("id") or data.get("jobId")
        if not job_id:
            print("❌ No job_id found in response!")
            return None
            
        return job_id
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error starting job: {e}")
        return None


def make_payment(job_id: str, amount: int, seller_wallet: str) -> bool:
    """
    Make payment through Masumi Payment Service
    """
    url = f"{MASUMI_PAYMENT_BASE_URL}/purchase/"
    headers = {
        "Authorization": f"Bearer {MASUMI_PAYMENT_TOKEN}",
        "token": MASUMI_PAYMENT_TOKEN,  # Some endpoints might expect this format
        "Content-Type": "application/json"
    }
    
    payload = {
        "identifier": job_id,
        "amount": amount,
        "currency": AGENT_PRICE_CURRENCY,
        "sellerWalletAddress": seller_wallet
    }
    
    print(f"💳 Making payment for job {job_id}...")
    print(f"💰 Amount: {amount} lovelace ({amount/1000000} ADA)")
    print(f"🏦 To wallet: {seller_wallet}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"📄 Payment response status: {response.status_code}")
        print(f"📄 Payment response: {response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            if data.get("status") == "success":
                print("✅ Payment submitted successfully!")
                return True
            else:
                print(f"❌ Payment failed: {data}")
                return False
        else:
            response.raise_for_status()
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error making payment: {e}")
        return False


def check_job_status(base_url: str, job_id: str) -> Optional[Dict[str, Any]]:
    """
    Check job status with Agent 118
    """
    # Try different possible status endpoint formats
    possible_urls = [
        f"{base_url}/status/{job_id}",
        f"{base_url}/status?job_id={job_id}",
        f"{base_url}/job/{job_id}/status",
        f"{base_url}/job/{job_id}"
    ]
    
    for url in possible_urls:
        try:
            print(f"🔍 Checking status at: {url}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"📄 Status response: {json.dumps(data, indent=2)}")
                return data
            else:
                print(f"❌ Status check failed with {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error checking status at {url}: {e}")
            continue
    
    print("❌ Could not check status at any endpoint")
    return None


def wait_for_completion(base_url: str, job_id: str, max_wait_time: int = 600) -> Optional[Dict[str, Any]]:
    """
    Wait for job completion and return results
    """
    print(f"⏳ Waiting for job {job_id} to complete (max {max_wait_time}s)...")
    
    start_time = time.time()
    check_interval = 30  # Check every 30 seconds
    
    while time.time() - start_time < max_wait_time:
        status_data = check_job_status(base_url, job_id)
        
        if status_data:
            status = status_data.get("status", "").lower()
            
            if status in ["completed", "success", "finished"]:
                print("🎉 Job completed!")
                return status_data
            elif status in ["failed", "error"]:
                print(f"💥 Job failed: {status_data}")
                return status_data
            elif status in ["running", "processing", "pending", "awaiting_payment"]:
                print(f"⏳ Job status: {status}")
            else:
                print(f"🤔 Unknown status: {status}")
        
        print(f"💤 Waiting {check_interval}s before next check...")
        time.sleep(check_interval)
    
    print(f"⏰ Timeout after {max_wait_time}s")
    return None


def main():
    """
    Main function to orchestrate the full workflow
    """
    if len(sys.argv) < 2:
        print("Usage: python call_masumi_agent.py '<message>'")
        print("Example: python call_masumi_agent.py 'Hello Echo Agent 320! Testing Masumi Network integration!'")
        return
    
    research_topic = sys.argv[1]
    
    print("🔊 Echo Agent 320 - Masumi Network Integration")
    print("=" * 50)
    
    # Step 0: Try to get current agent info from Registry
    registry_info = get_agent_info_from_registry(AGENT_ID)
    
    # Extract agent details (use fallback if registry fails)
    if registry_info:
        agent_url = registry_info.get("agentServiceApiEndpoint", FALLBACK_AGENT_API_BASE_URL)
        agent_price = registry_info.get("price", {}).get("amount", FALLBACK_AGENT_PRICE_LOVELACE)
        seller_wallet = registry_info.get("sellerWalletAddress")
    else:
        agent_url = FALLBACK_AGENT_API_BASE_URL
        agent_price = FALLBACK_AGENT_PRICE_LOVELACE
        seller_wallet = None
    
    # Get seller wallet from our payment service if not from registry
    if not seller_wallet:
        seller_wallet = get_wallet_from_payment_service()
        if not seller_wallet:
            print("❌ Could not determine seller wallet address")
            return
    
    print(f"🎯 Agent URL: {agent_url}")
    print(f"💰 Price: {agent_price} lovelace ({agent_price/1000000} ADA)")
    print(f"🏦 Seller wallet: {seller_wallet}")
    
    # Step 0.5: Test if agent is reachable
    if not test_agent_endpoint(agent_url):
        print("❌ Agent service appears to be down or unreachable")
        print("💡 This might be expected - some agents may not be always running")
        print("💡 You can still try the payment flow to see how it works")
        
        # Ask user if they want to continue anyway
        try:
            response = input("\n🤔 Continue anyway? (y/N): ").strip().lower()
            if response != 'y' and response != 'yes':
                return
        except KeyboardInterrupt:
            return
    
    # Step 1: Start the job
    job_id = start_agent_job(agent_url, research_topic)
    if not job_id:
        print("❌ Failed to start job")
        print("💡 This is expected if the agent service is not running")
        print("💡 For testing, you can use a mock job_id")
        
        # Use a mock job_id for testing payment flow
        job_id = f"test_job_{int(time.time())}"
        print(f"🧪 Using mock job_id for testing: {job_id}")
    
    print(f"\n🆔 Job ID: {job_id}")
    
    # Step 2: Make payment
    payment_success = make_payment(job_id, agent_price, seller_wallet)
    if not payment_success:
        print("❌ Failed to make payment")
        print("💡 Common reasons:")
        print("   - Insufficient funds in purchasing wallet")
        print("   - Wallet needs to be funded with Test-ADA")
        print("   - Network connectivity issues")
        return
    
    # Step 3: Wait for completion (only if job was actually started)
    if not job_id.startswith("test_job_"):
        print("\n⏳ Monitoring job progress...")
        final_result = wait_for_completion(agent_url, job_id)
        
        if final_result:
            print("\n🎯 Final Result:")
            print("=" * 50)
            
            # Try to extract the actual research result
            result = final_result.get("result") or final_result.get("output") or final_result.get("data")
            if result:
                print(result)
            else:
                print(json.dumps(final_result, indent=2))
        else:
            print("\n❌ No final result obtained")
    else:
        print("\n🧪 Test completed - payment flow worked!")
        print("💡 To complete a real job, the agent service needs to be running")


if __name__ == "__main__":
    main()
