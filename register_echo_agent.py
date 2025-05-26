#!/usr/bin/env python3
"""
Script to register the Echo Agent with Masumi Registry (Preprod)
Based on Masumi documentation for agent registration
"""

import requests
import json
import sys
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration - Update these values
MASUMI_PAYMENT_BASE_URL = os.getenv("MASUMI_PAYMENT_BASE_URL", "http://localhost:3001/api/v1")
MASUMI_PAYMENT_TOKEN = os.getenv("MASUMI_PAYMENT_TOKEN")

# Echo Agent Configuration
ECHO_AGENT_CONFIG = {
    "network": "Preprod",
    "ExampleOutputs": [
        {
            "name": "echo_example",
            "url": "https://example.com/echo_output.json",
            "mimeType": "application/json"
        }
    ],
    "Tags": [
        "echo",
        "test",
        "simple",
        "demo"
    ],
    "name": "Echo Agent",
    "description": "A simple echo agent that returns whatever message you send to it. Perfect for testing the Masumi Network integration.",
    "Author": {
        "name": "Pavel Larionov",
        "contactEmail": "pavel.larionov@nmkr.io",
        "contactOther": "github.com/pa1ar",
        "organization": "NMKR"
    },
    "apiBaseUrl": os.getenv("ECHO_AGENT_BASE_URL", "http://localhost:8000"),  # Where our echo agent is running
    "Legal": {
        "privacyPolicy": "https://nmkr.io/privacy",
        "terms": "https://nmkr.io/terms",
        "other": "https://nmkr.io/legal"
    },
    "sellingWalletVkey": "",  # Will be filled from payment service
    "Capability": {
        "name": "Echo Service",
        "version": "1.0.0"
    },
    "AgentPricing": {
        "pricingType": "Fixed",
        "Pricing": [
            {
                "unit": "",
                "amount": os.getenv("ECHO_AGENT_PRICE", "100000")  # 0.1 tADA in lovelace
            }
        ]
    }
}

def get_wallet_vkey() -> str:
    """Get the wallet verification key from the payment service"""
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
                        wallet_vkey = selling_wallets[0].get("walletVkey")
                        if wallet_vkey:
                            print(f"✅ Found wallet vkey: {wallet_vkey[:20]}...")
                            return wallet_vkey
        
        print("❌ No Preprod wallet vkey found in payment service")
        return ""
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting wallet vkey: {e}")
        return ""

def test_echo_agent() -> bool:
    """Test if the echo agent is running and responding"""
    try:
        response = requests.get(f"{ECHO_AGENT_CONFIG['apiBaseUrl']}/availability", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "available":
                print(f"✅ Echo agent is available: {data.get('message')}")
                return True
        
        print(f"❌ Echo agent not available: {response.status_code}")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach echo agent: {e}")
        return False

def register_agent(config: Dict[str, Any]) -> bool:
    """Register the agent with Masumi Registry"""
    url = f"{MASUMI_PAYMENT_BASE_URL}/registry/"
    headers = {
        "Authorization": f"Bearer {MASUMI_PAYMENT_TOKEN}",
        "token": MASUMI_PAYMENT_TOKEN,
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    print(f"🚀 Registering Echo Agent with Masumi Registry...")
    print(f"📍 URL: {url}")
    print(f"📝 Config: {json.dumps(config, indent=2)}")
    
    try:
        response = requests.post(url, json=config, headers=headers, timeout=30)
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            if data.get("status") == "success":
                print("🎉 Agent registered successfully!")
                agent_data = data.get("data", {})
                agent_id = agent_data.get("id")
                if agent_id:
                    print(f"🆔 Agent ID: {agent_id}")
                return True
            else:
                print(f"❌ Registration failed: {data}")
                return False
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error registering agent: {e}")
        return False

def main():
    """Main registration workflow"""
    print("🎯 Echo Agent Registration for Masumi Network")
    print("=" * 50)
    
    # Step 1: Test if echo agent is running
    print("\n📋 Step 1: Testing Echo Agent availability...")
    if not test_echo_agent():
        print("❌ Echo agent is not running!")
        print("💡 Please start the echo agent first:")
        print("   python echo_agent.py")
        return
    
    # Step 2: Get wallet verification key
    print("\n📋 Step 2: Getting wallet verification key...")
    wallet_vkey = get_wallet_vkey()
    if not wallet_vkey:
        print("❌ Could not get wallet verification key!")
        print("💡 Make sure your Masumi Payment Service is running and configured")
        return
    
    # Update config with wallet vkey
    ECHO_AGENT_CONFIG["sellingWalletVkey"] = wallet_vkey
    
    # Step 3: Register the agent
    print("\n📋 Step 3: Registering agent with Masumi Registry...")
    success = register_agent(ECHO_AGENT_CONFIG)
    
    if success:
        print("\n🎉 Registration completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Your agent should now be visible in the Masumi Registry")
        print("   2. Test calling your agent with the client script")
        print("   3. Check the Masumi Explorer for your agent")
    else:
        print("\n❌ Registration failed!")
        print("💡 Common issues:")
        print("   - Payment service not running")
        print("   - Invalid authentication token")
        print("   - Network connectivity issues")
        print("   - Wallet not properly configured")

if __name__ == "__main__":
    main() 