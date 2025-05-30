#!/usr/bin/env python3
"""
Script to call Echo Agent 320 through Masumi Network
This demonstrates the full workflow for calling a registered agent
"""

import requests
import time
import json
import sys
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Configuration from your environment
MASUMI_PAYMENT_BASE_URL = "http://localhost:3001/api/v1"
MASUMI_PAYMENT_TOKEN = os.getenv("MASUMI_PAYMENT_TOKEN")

# Echo Agent 320 information from registry metadata
AGENT_ID = "320"
AGENT_ASSET_ID = "0c2912d4088fbc6a0c725dbe5233735821109bd741acfa9f139023028d13b5832422b9245710c05f26b7b51a0dd6b9f1ead6b0e48e3b98a420851de1"
AGENT_API_BASE_URL = "http://localhost:8000"  # From onchainMetadata.api_base_url
AGENT_PRICE_LOVELACE = 10000  # From onchainMetadata.agentPricing.fixedPricing.amount
AGENT_PRICE_CURRENCY = "ADA"
NETWORK = "Preprod"

def get_agent_info_from_registry() -> Optional[Dict[str, Any]]:
    """
    Try to get agent information from Masumi Registry Service
    """
    registry_urls = [
        "https://registry.masumi.network",  # Official registry
        "https://api.masumi.network",       # API endpoint
        "http://localhost:3000"             # Local registry (if running)
    ]
    
    for base_url in registry_urls:
        try:
            # Try different possible endpoints for agent 320
            endpoints = [
                f"/agents/{AGENT_ID}",
                f"/api/v1/agents/{AGENT_ID}",
                f"/registry/agents/{AGENT_ID}",
                f"/payment-information/{AGENT_ID}"
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
    
    print("🤷 No registry service found, using hardcoded metadata")
    return None

def get_seller_wallet_from_payment_service() -> Optional[str]:
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
            payment_sources = data.get("data", {}).get("paymentSources", [])
            for source in payment_sources:
                if source.get("network") == NETWORK:
                    selling_wallets = source.get("SellingWallets", [])
                    if selling_wallets:
                        wallet_addr = selling_wallets[0].get("walletAddress")
                        print(f"📍 Found seller wallet: {wallet_addr}")
                        return wallet_addr
        
        print(f"❌ No {NETWORK} seller wallet found in payment service")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting wallet from payment service: {e}")
        return None

def test_agent_endpoint(base_url: str) -> bool:
    """
    Test if the echo agent endpoint is reachable
    """
    test_urls = [
        f"{base_url}/availability",
        f"{base_url}/health",
        f"{base_url}/",
    ]
    
    for url in test_urls:
        try:
            print(f"🩺 Testing: {url}")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Echo agent is reachable: {data}")
                return True
        except requests.exceptions.RequestException:
            continue
    
    print(f"❌ Echo agent not reachable at {base_url}")
    return False

def start_echo_job_direct(base_url: str, message: str) -> Optional[str]:
    """
    Start a job directly with the Echo Agent (bypassing payment)
    """
    url = f"{base_url.rstrip('/')}/start_job"
    
    payload = {
        "input_data": [
            {"key": "text", "value": message}
        ]
    }
    
    print(f"🚀 Starting job DIRECTLY with Echo Agent...")
    print(f"📍 URL: {url}")
    print(f"📝 Message: {message}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Job started successfully!")
        print(f"📄 Response: {json.dumps(data, indent=2)}")
        
        job_id = data.get("job_id")
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
    url = f"{MASUMI_PAYMENT_BASE_URL}/purchases"
    headers = {
        "Authorization": f"Bearer {MASUMI_PAYMENT_TOKEN}",
        "token": MASUMI_PAYMENT_TOKEN,
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
        
        if response.status_code in [200, 201]:
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
    Check job status with Echo Agent
    """
    url = f"{base_url}/status?job_id={job_id}"
    
    try:
        print(f"🔍 Checking status at: {url}")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Status response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"❌ Status check failed with {response.status_code}: {response.text}")
            return None
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking status: {e}")
        return None

def wait_for_completion(base_url: str, job_id: str, max_wait_time: int = 60) -> Optional[Dict[str, Any]]:
    """
    Wait for job completion and return results
    """
    print(f"⏳ Waiting for job {job_id} to complete (max {max_wait_time}s)...")
    
    start_time = time.time()
    check_interval = 5  # Check every 5 seconds
    
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
    Main function demonstrating both direct and payment-based access
    """
    if len(sys.argv) < 2:
        print("Usage: python call_echo_agent_320.py '<message>' [--direct]")
        print("Example: python call_echo_agent_320.py 'Hello, Echo Agent 320!'")
        print("         python call_echo_agent_320.py 'Hello!' --direct")
        return
    
    message = sys.argv[1]
    direct_mode = "--direct" in sys.argv
    
    print("🔊 Echo Agent 320 - Masumi Network Integration")
    print("=" * 60)
    print(f"🆔 Agent ID: {AGENT_ID}")
    print(f"🏷️  Asset ID: {AGENT_ASSET_ID}")
    print(f"🌐 Network: {NETWORK}")
    print(f"🎯 Agent URL: {AGENT_API_BASE_URL}")
    print(f"💰 Price: {AGENT_PRICE_LOVELACE} lovelace ({AGENT_PRICE_LOVELACE/1000000} ADA)")
    print("=" * 60)
    
    # Step 0: Try to get current agent info from Registry
    print("\n📋 Step 1: Checking Registry Service...")
    registry_info = get_agent_info_from_registry()
    
    # Step 0.5: Test if echo agent is reachable
    print("\n🩺 Step 2: Testing Agent Availability...")
    if not test_agent_endpoint(AGENT_API_BASE_URL):
        print("❌ Echo agent service appears to be down or unreachable")
        print("💡 Please start the echo agent first:")
        print("   cd agentic-service")
        print("   python echo_agent.py")
        return
    
    if direct_mode:
        print("\n🔓 DIRECT MODE: Bypassing payment system...")
        print("💡 This demonstrates that you CAN call the agent directly if you know the endpoint")
        
        # Start job directly
        job_id = start_echo_job_direct(AGENT_API_BASE_URL, message)
        if not job_id:
            print("❌ Failed to start job directly")
            return
        
        print(f"\n🆔 Job ID: {job_id}")
        
        # Check result directly
        final_result = wait_for_completion(AGENT_API_BASE_URL, job_id)
        
        if final_result:
            print("\n🎯 Final Result (Direct Access):")
            print("=" * 50)
            result = final_result.get("result")
            if result:
                print(f"🔊 Echo Response: {result}")
            else:
                print(json.dumps(final_result, indent=2))
        else:
            print("\n❌ No final result obtained")
            
    else:
        print("\n💳 PAYMENT MODE: Using Masumi Payment System...")
        
        # Get seller wallet
        print("\n💼 Step 3: Getting Seller Wallet...")
        seller_wallet = get_seller_wallet_from_payment_service()
        if not seller_wallet:
            print("❌ Could not determine seller wallet address")
            return
        
        # Start job
        print("\n🚀 Step 4: Starting Job...")
        job_id = start_echo_job_direct(AGENT_API_BASE_URL, message)
        if not job_id:
            print("❌ Failed to start job")
            return
        
        print(f"\n🆔 Job ID: {job_id}")
        
        # Make payment
        print("\n💳 Step 5: Making Payment...")
        payment_success = make_payment(job_id, AGENT_PRICE_LOVELACE, seller_wallet)
        if not payment_success:
            print("❌ Failed to make payment")
            print("💡 Common reasons:")
            print("   - Insufficient funds in purchasing wallet")
            print("   - Wallet needs to be funded with Test-ADA")
            print("   - Network connectivity issues")
            return
        
        # Wait for completion
        print("\n⏳ Step 6: Monitoring Job Progress...")
        final_result = wait_for_completion(AGENT_API_BASE_URL, job_id)
        
        if final_result:
            print("\n🎯 Final Result (Paid Access):")
            print("=" * 50)
            result = final_result.get("result")
            if result:
                print(f"🔊 Echo Response: {result}")
            else:
                print(json.dumps(final_result, indent=2))
        else:
            print("\n❌ No final result obtained")

if __name__ == "__main__":
    main() 