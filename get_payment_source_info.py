#!/usr/bin/env python3
"""
Script to get payment source information from Masumi Payment Service
This will help you get the SELLER_VKEY needed for your .env file
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_payment_source_info():
    """Get payment source information from the payment service"""
    payment_service_url = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:3001/api/v1")
    payment_api_key = os.getenv("PAYMENT_API_KEY", "myadminkeyisalsoverysafe")
    
    url = f"{payment_service_url}/payment-source/"
    headers = {
        "token": payment_api_key,
        "accept": "application/json"
    }
    
    print(f"🔍 Getting payment source info from: {url}")
    print(f"🔑 Using API key: {payment_api_key[:10]}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"📄 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Response data:")
            print(json.dumps(data, indent=2))
            
            if data.get("status") == "success":
                payment_sources = data.get("data", {}).get("PaymentSources", [])
                print(f"\n📄 Found {len(payment_sources)} payment sources")
                
                for source in payment_sources:
                    network = source.get("network")
                    print(f"\n📄 Network: {network}")
                    
                    if network == "Preprod":
                        selling_wallets = source.get("SellingWallets", [])
                        print(f"📄 Found {len(selling_wallets)} selling wallets")
                        
                        if selling_wallets:
                            wallet = selling_wallets[0]
                            wallet_addr = wallet.get("walletAddress")
                            wallet_vkey = wallet.get("walletVkey")
                            
                            print(f"\n✅ SELLER WALLET INFORMATION:")
                            print(f"   Address: {wallet_addr}")
                            print(f"   VKey: {wallet_vkey}")
                            print(f"\n📝 Add this to your .env file:")
                            print(f"   SELLER_VKEY={wallet_vkey}")
                            
                            return {
                                "wallet_address": wallet_addr,
                                "vkey": wallet_vkey
                            }
                
                print("❌ No Preprod selling wallets found")
                return None
            else:
                print(f"❌ Payment source request failed: {data}")
                return None
        else:
            print(f"❌ Payment source error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting payment source info: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🎯 Getting Masumi Payment Source Information")
    print("=" * 50)
    
    result = get_payment_source_info()
    
    if result:
        print("\n🎉 Successfully retrieved payment source information!")
    else:
        print("\n❌ Failed to get payment source information.")
        print("💡 Make sure:")
        print("   - Masumi Payment Service is running on port 3001")
        print("   - Your API key is correct in .env file")
        print("   - You have a configured payment source for Preprod network") 