#!/usr/bin/env python3
"""
Script to call our Echo Agent through Masumi Network
This demonstrates the full workflow: discovery, job start, payment, and result retrieval
"""

import requests
import time
import json
import sys
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from your environment
MASUMI_PAYMENT_BASE_URL = os.getenv("MASUMI_PAYMENT_BASE_URL", "http://localhost:3001/api/v1")
MASUMI_PAYMENT_TOKEN = os.getenv("MASUMI_PAYMENT_TOKEN")

# Echo Agent information
ECHO_AGENT_API_BASE_URL = os.getenv("ECHO_AGENT_BASE_URL", "http://localhost:8000")
ECHO_AGENT_PRICE_LOVELACE = int(os.getenv("ECHO_AGENT_PRICE", "100000"))  # 0.1 tADA
AGENT_PRICE_CURRENCY = "ADA"

def get_echo_agent_info_from_registry() -> Optional[Dict[str, Any]]:
    """
    Try to get our echo agent information from Registry Service
    """
    # Try to find our echo agent in the registry
    registry_urls = [
        "http://localhost:3000",  # Local registry
        "https://registry.masumi.network",  # Official registry
        "https://api.masumi.network"  # API endpoint
    ]
    
    for base_url in registry_urls:
        try:
            # Try to list all agents and find ours
            endpoints = [
                "/agents",
                "/registry/agents",
                "/api/v1/agents"
            ]
            
            for endpoint in endpoints:
                url = f"{base_url}{endpoint}"
                print(f"🔍 Trying registry: {url}")
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Look for our echo agent
                    agents = data if isinstance(data, list) else data.get("data", [])
                    for agent in agents:
                        if isinstance(agent, dict) and agent.get("name") == "Echo Agent":
                            print(f"✅ Found Echo Agent: {json.dumps(agent, indent=2)}")
                            return agent
                    
                    print(f"🔍 Registry found but no Echo Agent in {len(agents)} agents")
                else:
                    print(f"❌ {response.status_code}: {response.text[:100]}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ Registry check failed for {base_url}: {e}")
            continue
    
    print("🤷 No registry service found or Echo Agent not registered, using direct connection")
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

def test_echo_agent_endpoint(base_url: str) -> bool:
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

def start_echo_job(base_url: str, message: str) -> Optional[str]:
    """
    Start a job with our Echo Agent
    """
    url = f"{base_url.rstrip('/')}/start_job"
    
    # Based on our echo agent's input schema
    payload = {
        "input_data": [
            {"key": "text", "value": message}
        ]
    }
    
    print(f"🚀 Starting job with Echo Agent...")
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
    check_interval = 5  # Check every 5 seconds for echo agent
    
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
        print("Usage: python call_echo_agent.py '<message>'")
        print("Example: python call_echo_agent.py 'Hello, Echo Agent! How are you today?'")
        return
    
    message = sys.argv[1]
    
    print("🔊 Echo Agent Test - Masumi Network Integration")
    print("=" * 50)
    
    # Step 0: Try to get current agent info from Registry
    registry_info = get_echo_agent_info_from_registry()
    
    # Extract agent details (use fallback if registry fails)
    if registry_info:
        agent_url = registry_info.get("apiBaseUrl", ECHO_AGENT_API_BASE_URL)
        agent_price = registry_info.get("AgentPricing", {}).get("Pricing", [{}])[0].get("amount", ECHO_AGENT_PRICE_LOVELACE)
        seller_wallet = registry_info.get("SmartContractWallet", {}).get("walletAddress")
    else:
        agent_url = ECHO_AGENT_API_BASE_URL
        agent_price = ECHO_AGENT_PRICE_LOVELACE
        seller_wallet = None
    
    # Get seller wallet from our payment service if not from registry
    if not seller_wallet:
        seller_wallet = get_wallet_from_payment_service()
        if not seller_wallet:
            print("❌ Could not determine seller wallet address")
            return
    
    print(f"🎯 Agent URL: {agent_url}")
    print(f"💰 Price: {agent_price} lovelace ({int(agent_price)/1000000} ADA)")
    print(f"🏦 Seller wallet: {seller_wallet}")
    
    # Step 0.5: Test if echo agent is reachable
    if not test_echo_agent_endpoint(agent_url):
        print("❌ Echo agent service appears to be down or unreachable")
        print("💡 Please start the echo agent first:")
        print("   python echo_agent.py")
        return
    
    # Step 1: Start the job
    job_id = start_echo_job(agent_url, message)
    if not job_id:
        print("❌ Failed to start job")
        return
    
    print(f"\n🆔 Job ID: {job_id}")
    
    # Step 2: Make payment
    payment_success = make_payment(job_id, int(agent_price), seller_wallet)
    if not payment_success:
        print("❌ Failed to make payment")
        print("💡 Common reasons:")
        print("   - Insufficient funds in purchasing wallet")
        print("   - Wallet needs to be funded with Test-ADA")
        print("   - Network connectivity issues")
        return
    
    # Step 3: Wait for completion
    print("\n⏳ Monitoring job progress...")
    final_result = wait_for_completion(agent_url, job_id)
    
    if final_result:
        print("\n🎯 Final Result:")
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