#!/usr/bin/env python3
"""
Script to check wallet balances for Masumi Payment Service
Checks both selling and purchasing wallets on Preprod
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MASUMI_PAYMENT_BASE_URL = os.getenv("MASUMI_PAYMENT_BASE_URL", "http://localhost:3001/api/v1")
MASUMI_PAYMENT_TOKEN = os.getenv("MASUMI_PAYMENT_TOKEN")

def check_payment_sources():
    """Get payment source information including wallet addresses and balances"""
    url = f"{MASUMI_PAYMENT_BASE_URL}/payment-source/"
    headers = {
        "accept": "application/json",
        "token": MASUMI_PAYMENT_TOKEN
    }
    
    try:
        print("🔍 Checking payment sources...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") == "success":
            payment_sources = data.get("data", {}).get("PaymentSources", [])
            
            for source in payment_sources:
                network = source.get("network")
                if network == "Preprod":
                    print(f"\n🌐 Network: {network}")
                    
                    # Check selling wallets
                    selling_wallets = source.get("SellingWallets", [])
                    if selling_wallets:
                        print("\n💰 Selling Wallets:")
                        for i, wallet in enumerate(selling_wallets):
                            addr = wallet.get("walletAddress", "N/A")
                            vkey = wallet.get("walletVkey", "N/A")
                            print(f"  Wallet {i+1}:")
                            print(f"    Address: {addr}")
                            print(f"    VKey: {vkey[:20]}..." if len(vkey) > 20 else f"    VKey: {vkey}")
                    
                    # Check purchasing wallets
                    purchasing_wallets = source.get("PurchasingWallets", [])
                    if purchasing_wallets:
                        print("\n🛒 Purchasing Wallets:")
                        for i, wallet in enumerate(purchasing_wallets):
                            addr = wallet.get("walletAddress", "N/A")
                            vkey = wallet.get("walletVkey", "N/A")
                            print(f"  Wallet {i+1}:")
                            print(f"    Address: {addr}")
                            print(f"    VKey: {vkey[:20]}..." if len(vkey) > 20 else f"    VKey: {vkey}")
                    
                    return source
        
        print("❌ No payment sources found or invalid response")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting payment sources: {e}")
        return None

def check_wallet_balance(wallet_address: str, wallet_type: str):
    """Check the balance of a specific wallet"""
    # Try different wallet endpoints
    endpoints = [
        f"/wallet/{wallet_address}/balance",
        f"/wallets/{wallet_address}/balance",
        f"/wallet/balance?address={wallet_address}"
    ]
    
    headers = {
        "accept": "application/json",
        "token": MASUMI_PAYMENT_TOKEN
    }
    
    for endpoint in endpoints:
        try:
            url = f"{MASUMI_PAYMENT_BASE_URL}{endpoint}"
            print(f"🔍 Trying: {url}")
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {wallet_type} Balance Response: {json.dumps(data, indent=2)}")
                return data
            else:
                print(f"❌ {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error checking balance at {endpoint}: {e}")
            continue
    
    print(f"❌ Could not check balance for {wallet_type} wallet")
    return None

def check_utxos():
    """Check UTXOs for all wallets"""
    url = f"{MASUMI_PAYMENT_BASE_URL}/utxos/"
    headers = {
        "accept": "application/json",
        "token": MASUMI_PAYMENT_TOKEN
    }
    
    try:
        print("\n🔍 Checking UTXOs...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        print(f"📊 UTXOs Response: {json.dumps(data, indent=2)}")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting UTXOs: {e}")
        return None

def main():
    """Main function to check all wallet information"""
    print("💳 Masumi Wallet Balance Checker")
    print("=" * 50)
    
    if not MASUMI_PAYMENT_TOKEN:
        print("❌ MASUMI_PAYMENT_TOKEN not set in .env file")
        print("💡 Please add your admin token to the .env file")
        return
    
    # Step 1: Get payment source information
    payment_source = check_payment_sources()
    
    if not payment_source:
        print("❌ Could not get payment source information")
        return
    
    # Step 2: Check UTXOs (this might show balances)
    check_utxos()
    
    # Step 3: Try to check individual wallet balances
    selling_wallets = payment_source.get("SellingWallets", [])
    purchasing_wallets = payment_source.get("PurchasingWallets", [])
    
    if selling_wallets:
        print(f"\n💰 Checking Selling Wallet Balance...")
        wallet_addr = selling_wallets[0].get("walletAddress")
        if wallet_addr:
            check_wallet_balance(wallet_addr, "Selling")
    
    if purchasing_wallets:
        print(f"\n🛒 Checking Purchasing Wallet Balance...")
        wallet_addr = purchasing_wallets[0].get("walletAddress")
        if wallet_addr:
            check_wallet_balance(wallet_addr, "Purchasing")
    
    print("\n💡 Next steps:")
    print("   - If balances are 0, fund wallets using the Cardano Faucet")
    print("   - Visit: https://docs.cardano.org/cardano-testnet/tools/faucet/")
    print("   - Or use the admin dashboard: http://localhost:3001/admin/")

if __name__ == "__main__":
    main() 