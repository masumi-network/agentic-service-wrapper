#!/usr/bin/env python3
"""
Client for Echo Agent - No Payment Node Required
This demonstrates how users can interact with Masumi agents using only:
1. Standard Cardano wallet tools (like cardano-cli)
2. Direct blockchain transactions
3. No Masumi payment node needed on client side
"""

import requests
import time
import json
import sys
import subprocess
import os
from typing import Dict, Any, Optional

# Configuration
ECHO_AGENT_BASE_URL = "http://localhost:8000"
CARDANO_CLI = "cardano-cli"  # Assumes cardano-cli is in PATH
NETWORK = "testnet-magic 1"  # Preprod testnet

class CardanoWalletClient:
    """
    Simple Cardano wallet client using cardano-cli
    In production, you'd use libraries like PyCardano or similar
    """
    
    def __init__(self, wallet_dir: str):
        self.wallet_dir = wallet_dir
        self.payment_skey = os.path.join(wallet_dir, "payment.skey")
        self.payment_vkey = os.path.join(wallet_dir, "payment.vkey")
        self.payment_addr = os.path.join(wallet_dir, "payment.addr")
        
    def get_wallet_address(self) -> str:
        """Get the wallet address"""
        if os.path.exists(self.payment_addr):
            with open(self.payment_addr, 'r') as f:
                return f.read().strip()
        raise Exception("Wallet address file not found")
    
    def get_utxos(self) -> list:
        """Get UTXOs for the wallet"""
        addr = self.get_wallet_address()
        cmd = [
            CARDANO_CLI, "query", "utxo",
            "--address", addr,
            f"--{NETWORK}",
            "--out-file", "/dev/stdout"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error getting UTXOs: {e}")
            return {}
    
    def build_payment_transaction(self, recipient_addr: str, amount_lovelace: int, 
                                metadata: Dict[str, Any]) -> str:
        """
        Build a transaction to pay for Masumi service
        This is where the magic happens - direct blockchain payment
        """
        utxos = self.get_utxos()
        if not utxos:
            raise Exception("No UTXOs available")
        
        # Select UTXO with enough funds
        selected_utxo = None
        for txhash_ix, utxo_data in utxos.items():
            if utxo_data["value"]["lovelace"] >= amount_lovelace + 200000:  # +fee
                selected_utxo = (txhash_ix, utxo_data)
                break
        
        if not selected_utxo:
            raise Exception("Insufficient funds")
        
        txhash_ix, utxo_data = selected_utxo
        txhash, ix = txhash_ix.split("#")
        
        # Create metadata file
        metadata_file = "/tmp/metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        # Build transaction
        tx_raw = "/tmp/tx.raw"
        sender_addr = self.get_wallet_address()
        
        cmd = [
            CARDANO_CLI, "transaction", "build",
            "--tx-in", f"{txhash}#{ix}",
            "--tx-out", f"{recipient_addr}+{amount_lovelace}",
            "--change-address", sender_addr,
            "--metadata-json-file", metadata_file,
            f"--{NETWORK}",
            "--out-file", tx_raw
        ]
        
        try:
            subprocess.run(cmd, check=True)
            return tx_raw
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to build transaction: {e}")
    
    def sign_and_submit_transaction(self, tx_raw: str) -> str:
        """Sign and submit the transaction"""
        tx_signed = "/tmp/tx.signed"
        
        # Sign transaction
        sign_cmd = [
            CARDANO_CLI, "transaction", "sign",
            "--tx-body-file", tx_raw,
            "--signing-key-file", self.payment_skey,
            f"--{NETWORK}",
            "--out-file", tx_signed
        ]
        
        subprocess.run(sign_cmd, check=True)
        
        # Submit transaction
        submit_cmd = [
            CARDANO_CLI, "transaction", "submit",
            "--tx-file", tx_signed,
            f"--{NETWORK}"
        ]
        
        result = subprocess.run(submit_cmd, capture_output=True, text=True, check=True)
        
        # Get transaction hash
        txhash_cmd = [
            CARDANO_CLI, "transaction", "txid",
            "--tx-file", tx_signed
        ]
        
        txhash_result = subprocess.run(txhash_cmd, capture_output=True, text=True, check=True)
        return txhash_result.stdout.strip()

class MasumiAgentClient:
    """
    Client for interacting with Masumi agents without running a payment node
    """
    
    def __init__(self, agent_base_url: str, wallet_client: CardanoWalletClient):
        self.agent_base_url = agent_base_url
        self.wallet = wallet_client
    
    def start_job(self, message: str) -> Dict[str, Any]:
        """Start a job with the agent and get payment information"""
        url = f"{self.agent_base_url}/start_job"
        payload = {
            "input_data": [
                {"key": "text", "value": message}
            ]
        }
        
        print(f"🚀 Starting job with agent...")
        print(f"📝 Message: {message}")
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Job started! Payment required.")
        print(f"📄 Response: {json.dumps(data, indent=2)}")
        
        return data
    
    def make_payment(self, job_info: Dict[str, Any]) -> str:
        """
        Make payment directly to Cardano blockchain
        This is the key difference - no Masumi payment node needed!
        """
        # Extract payment information from job response
        job_id = job_info["blockchainIdentifier"]
        seller_wallet = job_info["sellerWalletAddress"]
        amounts = job_info["amounts"]
        
        # Find ADA amount
        ada_amount = None
        for amount in amounts:
            if amount["unit"] == "lovelace":
                ada_amount = int(amount["amount"])
                break
        
        if not ada_amount:
            raise Exception("No ADA amount found in payment info")
        
        print(f"💳 Making direct blockchain payment...")
        print(f"💰 Amount: {ada_amount} lovelace ({ada_amount/1000000} ADA)")
        print(f"🏦 To: {seller_wallet}")
        print(f"🔗 Job ID: {job_id}")
        
        # Create metadata for the transaction
        # This is how Masumi tracks which payment is for which job
        metadata = {
            "674": {  # Masumi metadata label
                "job_id": job_id,
                "service": "echo_agent",
                "version": "1.0"
            }
        }
        
        # Build, sign, and submit transaction
        tx_raw = self.wallet.build_payment_transaction(
            recipient_addr=seller_wallet,
            amount_lovelace=ada_amount,
            metadata=metadata
        )
        
        tx_hash = self.wallet.sign_and_submit_transaction(tx_raw)
        
        print(f"✅ Payment submitted!")
        print(f"🔗 Transaction hash: {tx_hash}")
        
        return tx_hash
    
    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a job"""
        url = f"{self.agent_base_url}/status"
        params = {"job_id": job_id}
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    def wait_for_completion(self, job_id: str, max_wait: int = 300) -> Optional[Dict[str, Any]]:
        """Wait for job completion"""
        print(f"⏳ Waiting for job {job_id} to complete...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status = self.check_job_status(job_id)
            
            job_status = status.get("status", "").lower()
            payment_status = status.get("payment_status", "").lower()
            
            print(f"📊 Job: {job_status}, Payment: {payment_status}")
            
            if job_status == "completed":
                print("🎉 Job completed!")
                return status
            elif job_status == "failed":
                print("💥 Job failed!")
                return status
            
            time.sleep(10)  # Check every 10 seconds
        
        print("⏰ Timeout waiting for completion")
        return None

def setup_example_wallet():
    """
    Example of how to set up a wallet for testing
    In practice, users would have their own wallets
    """
    wallet_dir = "/tmp/test_wallet"
    os.makedirs(wallet_dir, exist_ok=True)
    
    # Generate keys if they don't exist
    skey_path = os.path.join(wallet_dir, "payment.skey")
    vkey_path = os.path.join(wallet_dir, "payment.vkey")
    addr_path = os.path.join(wallet_dir, "payment.addr")
    
    if not os.path.exists(skey_path):
        print("🔑 Generating test wallet...")
        
        # Generate payment key pair
        subprocess.run([
            CARDANO_CLI, "address", "key-gen",
            "--verification-key-file", vkey_path,
            "--signing-key-file", skey_path
        ], check=True)
        
        # Generate address
        subprocess.run([
            CARDANO_CLI, "address", "build",
            "--payment-verification-key-file", vkey_path,
            f"--{NETWORK}",
            "--out-file", addr_path
        ], check=True)
        
        with open(addr_path, 'r') as f:
            addr = f.read().strip()
        
        print(f"✅ Wallet generated!")
        print(f"📍 Address: {addr}")
        print(f"💡 Fund this address with test ADA from: https://docs.cardano.org/cardano-testnet/tools/faucet")
    
    return wallet_dir

def main():
    """
    Main function demonstrating the complete flow
    """
    if len(sys.argv) < 2:
        print("Usage: python client_without_payment_node.py '<message>'")
        print("Example: python client_without_payment_node.py 'Hello Echo Agent!'")
        return
    
    message = sys.argv[1]
    
    print("🔊 Echo Agent Client - Direct Blockchain Payment")
    print("=" * 60)
    print("💡 This client does NOT require a Masumi payment node!")
    print("💡 It pays directly to the Cardano blockchain")
    print("=" * 60)
    
    try:
        # Setup wallet (in practice, user already has one)
        wallet_dir = setup_example_wallet()
        wallet_client = CardanoWalletClient(wallet_dir)
        
        # Check wallet balance
        utxos = wallet_client.get_utxos()
        if not utxos:
            addr = wallet_client.get_wallet_address()
            print(f"❌ No funds in wallet!")
            print(f"📍 Please fund address: {addr}")
            print(f"🔗 Faucet: https://docs.cardano.org/cardano-testnet/tools/faucet")
            return
        
        # Create agent client
        agent_client = MasumiAgentClient(ECHO_AGENT_BASE_URL, wallet_client)
        
        # Step 1: Start job and get payment info
        job_info = agent_client.start_job(message)
        job_id = job_info["blockchainIdentifier"]
        
        # Step 2: Make direct blockchain payment
        tx_hash = agent_client.make_payment(job_info)
        
        # Step 3: Wait for completion
        final_result = agent_client.wait_for_completion(job_id)
        
        if final_result and final_result.get("result"):
            print("\n🎯 Final Result:")
            print("=" * 50)
            print(f"🔊 {final_result['result']}")
        else:
            print("\n❌ No result obtained")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Cardano CLI error: {e}")
        print("💡 Make sure cardano-cli is installed and in PATH")
        print("💡 Install from: https://docs.cardano.org/getting-started/installing-the-cardano-node")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 