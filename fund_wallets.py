#!/usr/bin/env python3
"""
Script to help fund Masumi wallets using the Cardano Faucet
Provides wallet addresses and faucet links for easy funding
"""

import requests
import json
import os
import webbrowser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MASUMI_PAYMENT_BASE_URL = os.getenv("MASUMI_PAYMENT_BASE_URL", "http://localhost:3001/api/v1")
MASUMI_PAYMENT_TOKEN = os.getenv("MASUMI_PAYMENT_TOKEN")
CARDANO_FAUCET_URL = "https://docs.cardano.org/cardano-testnet/tools/faucet/"

def get_wallet_addresses():
    """Get wallet addresses from payment service"""
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
                    return source
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting payment sources: {e}")
        return None

def fund_wallet_via_faucet(wallet_address: str, wallet_type: str):
    """Provide instructions and links to fund a wallet"""
    print(f"\n💰 Funding {wallet_type} Wallet")
    print("=" * 50)
    print(f"📍 Wallet Address: {wallet_address}")
    print(f"🔗 Cardano Faucet: {CARDANO_FAUCET_URL}")
    
    print("\n📋 Steps to fund this wallet:")
    print("1. Copy the wallet address above")
    print("2. Visit the Cardano Faucet (link above)")
    print("3. Select 'Preprod Testnet' from the Environment dropdown")
    print("4. Paste the wallet address in the 'Address' field")
    print("5. Click 'Request Funds'")
    print("6. Wait 2-3 minutes for the transaction to complete")
    
    # Ask if user wants to open the faucet
    try:
        response = input(f"\n🌐 Open Cardano Faucet in browser for {wallet_type} wallet? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            webbrowser.open(CARDANO_FAUCET_URL)
            print("✅ Opened faucet in browser")
    except KeyboardInterrupt:
        print("\n⏹️ Skipped opening browser")

def check_utxos_for_address(address: str):
    """Check UTXOs for a specific address"""
    url = f"{MASUMI_PAYMENT_BASE_URL}/utxos/"
    headers = {
        "accept": "application/json",
        "token": MASUMI_PAYMENT_TOKEN
    }
    
    params = {
        "address": address,
        "network": "Preprod"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                utxos = data.get("data", [])
                total_lovelace = sum(int(utxo.get("amount", 0)) for utxo in utxos)
                total_ada = total_lovelace / 1000000
                
                print(f"✅ Found {len(utxos)} UTXOs")
                print(f"💰 Total balance: {total_lovelace} lovelace ({total_ada:.2f} ADA)")
                return total_lovelace > 0
            else:
                print(f"❌ Error: {data}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:100]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking UTXOs: {e}")
        return False

def main():
    """Main function to help fund wallets"""
    print("💳 Masumi Wallet Funding Helper")
    print("=" * 50)
    
    if not MASUMI_PAYMENT_TOKEN:
        print("❌ MASUMI_PAYMENT_TOKEN not set in .env file")
        return
    
    # Get wallet addresses
    payment_source = get_wallet_addresses()
    if not payment_source:
        print("❌ Could not get wallet addresses")
        return
    
    selling_wallets = payment_source.get("SellingWallets", [])
    purchasing_wallets = payment_source.get("PurchasingWallets", [])
    
    if not selling_wallets or not purchasing_wallets:
        print("❌ No wallets found")
        return
    
    selling_addr = selling_wallets[0].get("walletAddress")
    purchasing_addr = purchasing_wallets[0].get("walletAddress")
    
    print("🔍 Current wallet status:")
    
    # Check selling wallet
    print(f"\n💰 Selling Wallet: {selling_addr[:20]}...")
    has_selling_funds = check_utxos_for_address(selling_addr)
    
    # Check purchasing wallet  
    print(f"\n🛒 Purchasing Wallet: {purchasing_addr[:20]}...")
    has_purchasing_funds = check_utxos_for_address(purchasing_addr)
    
    # Fund wallets if needed
    if not has_selling_funds:
        print("\n⚠️  Selling wallet needs funding!")
        fund_wallet_via_faucet(selling_addr, "Selling")
    else:
        print("\n✅ Selling wallet has funds")
    
    if not has_purchasing_funds:
        print("\n⚠️  Purchasing wallet needs funding!")
        fund_wallet_via_faucet(purchasing_addr, "Purchasing")
    else:
        print("\n✅ Purchasing wallet has funds")
    
    if has_selling_funds and has_purchasing_funds:
        print("\n🎉 Both wallets are funded!")
        print("💡 You can now try registering your agent again")
        print("🌐 Admin dashboard: http://localhost:3001/admin/")
    else:
        print("\n⏳ After funding, wait 2-3 minutes then run this script again to verify")

if __name__ == "__main__":
    main() 