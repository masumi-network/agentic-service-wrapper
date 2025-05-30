#!/usr/bin/env python3
"""
Advanced Masumi Agent Client using PyCardano
This shows how to interact with Masumi agents using proper Python libraries
No Masumi payment node required on client side!
"""

import requests
import time
import json
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass
import os

try:
    from pycardano import (
        PaymentSigningKey, PaymentVerificationKey, Address, Network,
        TransactionBuilder, TransactionOutput, Value, AuxiliaryData, Metadata,
        ChainContext, BlockFrostChainContext
    )
    PYCARDANO_AVAILABLE = True
except ImportError:
    PYCARDANO_AVAILABLE = False
    print("⚠️  PyCardano not available. Install with: pip install pycardano")

@dataclass
class WalletConfig:
    """Configuration for a Cardano wallet"""
    # signing_key: str  # Hex-encoded signing key - REMOVED, using file path instead
    network: Network = Network.TESTNET
    blockfrost_project_id: Optional[str] = None
    signing_key_file: Optional[str] = "payment.skey" # Field for skey file path

class PyCardanoWalletClient:
    """
    Advanced Cardano wallet client using PyCardano
    This is the recommended approach for production applications
    """
    
    def __init__(self, config: WalletConfig):
        if not PYCARDANO_AVAILABLE:
            raise Exception("PyCardano library not available")
        
        self.config = config
        # self.signing_key = PaymentSigningKey.from_extended_cbor(config.signing_key)
        
        # Load the signing key from the file specified in config
        try:
            print(f"INFO: Attempting to load signing key from file: {config.signing_key_file}")
            self.signing_key = PaymentSigningKey.load(config.signing_key_file)
            print("INFO: Signing key loaded successfully from file.")
        except Exception as e:
            print(f"❌ Error loading signing key from file '{config.signing_key_file}': {e}")
            print("💡 Please ensure the file exists and contains a valid PyCardano signing key.")
            print("   You can generate one using the example snippet provided in the previous messages.")
            raise ValueError("Failed to load signing key from file.") from e

        self.verification_key = PaymentVerificationKey.from_signing_key(self.signing_key)
        self.address = Address(self.verification_key.hash(), network=config.network)
        
        # Setup chain context (for querying blockchain)
        if config.blockfrost_project_id:
            self.context = BlockFrostChainContext(
                project_id=config.blockfrost_project_id,
                network=config.network
            )
        else:
            # For demo purposes, we'll use a mock context
            # In production, you need a proper chain context
            self.context = None
            print("⚠️  No BlockFrost project ID provided. Some features may not work without a live chain context.")
    
    def get_address(self) -> str:
        """Get the wallet address"""
        return str(self.address)
    
    def get_utxos(self):
        """Get UTXOs for the wallet"""
        if not self.context:
            raise Exception("Chain context not available. Please provide a Blockfrost Project ID.")
        print(f"DEBUG: Querying UTxOs for address: {str(self.address)} via Blockfrost...")
        utxos = self.context.utxos(str(self.address))
        print(f"DEBUG: Received {len(utxos)} UTxOs from Blockfrost.")
        return utxos

    def check_balance(self):
        """Checks and prints the balance of the wallet."""
        if not self.context:
            print("⚠️ Cannot check balance: Chain context not available (Blockfrost Project ID missing or invalid).")
            return None, []

        print(f"\n💰 Checking balance for address: {self.get_address()}")
        try:
            utxos = self.get_utxos()
            total_lovelace = 0
            if not utxos:
                print("  No UTxOs found for this address.")
            else:
                print(f"  Found {len(utxos)} UTxO(s):")
                for i, utxo in enumerate(utxos):
                    print(f"    UTxO {i+1}:")
                    print(f"      TxHash: {utxo.input.transaction_id}")
                    print(f"      TxIndex: {utxo.input.index}")
                    print(f"      Amount: {utxo.output.amount.coin} lovelace")
                    if utxo.output.amount.multi_asset:
                        print(f"      MultiAsset: {utxo.output.amount.multi_asset}")
                    total_lovelace += utxo.output.amount.coin
            
            total_ada = total_lovelace / 1_000_000
            print(f"  -------------------------------------")
            print(f"  Total Balance: {total_lovelace} lovelace ({total_ada:.6f} ADA)")
            print(f"  -------------------------------------")
            return total_lovelace, utxos
        except Exception as e:
            print(f"❌ Error checking balance: {e}")
            print("   This could be due to network issues, an invalid Blockfrost Project ID, or the address not being found on the blockchain yet.")
            return None, []

    def build_payment_transaction(self, recipient_addr: str, amount_lovelace: int, 
                                metadata: Dict[str, Any]) -> bytes:
        """
        Build a transaction to pay for Masumi service
        Returns the signed transaction bytes
        """
        if not self.context:
            raise Exception("Chain context not available for transaction building. Please provide a Blockfrost Project ID.")
        
        # Create transaction builder
        builder = TransactionBuilder(self.context)
        
        # Explicitly fetch UTxOs and add them to the builder
        print(f"DEBUG: Explicitly fetching UTxOs for builder for address: {self.address}")
        input_utxos = self.get_utxos() # Reuses the existing method that queries Blockfrost
        if not input_utxos:
            # This should ideally be caught by check_balance earlier, but good to have a guard here.
            raise ValueError(f"No UTxOs found for address {self.address}. Cannot build transaction.")
        print(f"DEBUG: Found {len(input_utxos)} UTxO(s). Adding them to the builder.")
        for i, utxo_to_add in enumerate(input_utxos):
            builder.add_input(utxo_to_add)
            print(f"DEBUG: Added UTxO {i+1} to builder: TxHash={utxo_to_add.input.transaction_id}, Index={utxo_to_add.input.index}, Amount={utxo_to_add.output.amount.coin}")
        print(f"DEBUG: Finished adding {len(input_utxos)} UTxO(s) to builder.")
        
        # Add recipient output
        recipient_address = Address.from_primitive(recipient_addr)
        output = TransactionOutput(recipient_address, Value(amount_lovelace))
        builder.add_output(output)
        
        # Add metadata
        aux_data = AuxiliaryData(data=Metadata(metadata))
        builder.auxiliary_data = aux_data
        
        # Build and sign transaction
        signed_tx = builder.build_and_sign([self.signing_key], change_address=self.address)
        
        return signed_tx.to_cbor()
    
    def submit_transaction(self, tx_cbor: bytes) -> str:
        """Submit transaction and return transaction hash"""
        if not self.context:
            raise Exception("Chain context not available for transaction submission. Please provide a Blockfrost Project ID.")
        
        return self.context.submit_tx(tx_cbor)

class MasumiAgentClientAdvanced:
    """
    Advanced client for interacting with Masumi agents
    Uses PyCardano for proper blockchain integration
    """
    
    def __init__(self, agent_base_url: str, wallet_client: PyCardanoWalletClient):
        self.agent_base_url = agent_base_url
        self.wallet = wallet_client
    
    def discover_agent_from_registry(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Discover agent information from Masumi registry
        This is the proper way to find agents in the network
        """
        registry_urls = [
            "http://localhost:3000",  # Local registry
            "https://registry.masumi.network",  # Official registry
        ]
        
        for base_url in registry_urls:
            try:
                url = f"{base_url}/payment-information/{agent_id}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException:
                continue
        
        return None
    
    def start_job(self, message: str) -> Dict[str, Any]:
        """Start a job with the agent"""
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
        
        return data
    
    def make_payment(self, job_info: Dict[str, Any]) -> str:
        """
        Make payment using PyCardano
        This demonstrates the proper way to pay for Masumi services
        """
        # Extract payment information
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
        
        print(f"💳 Making blockchain payment with PyCardano...")
        print(f"💰 Amount: {ada_amount} lovelace ({ada_amount/1000000} ADA)")
        print(f"🏦 To: {seller_wallet}")
        print(f"🔗 Job ID: {job_id}")
        
        # Create Masumi-compatible metadata
        # This follows the Masumi protocol specification
        metadata = {
            674: {  # Masumi metadata label (CIP-25 compatible)
                "job_id": job_id,
                "service": "echo_agent",
                "version": "1.0",
                "timestamp": int(time.time()),
                "client": "pycardano_client"
            }
        }
        
        # Build and submit transaction
        tx_cbor = self.wallet.build_payment_transaction(
            recipient_addr=seller_wallet,
            amount_lovelace=ada_amount,
            metadata=metadata
        )
        
        tx_hash = self.wallet.submit_transaction(tx_cbor)
        
        print(f"✅ Payment submitted!")
        print(f"🔗 Transaction hash: {tx_hash}")
        
        return tx_hash
    
    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check job status"""
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
            
            time.sleep(10)
        
        print("⏰ Timeout waiting for completion")
        return None

def create_example_wallet_config() -> WalletConfig:
    """
    Create an example wallet configuration
    In practice, users would load this from secure storage
    """
    # Generate a new signing key for demo
    # In production, users would have existing keys
    if PYCARDANO_AVAILABLE:
        # from pycardano import PaymentSigningKey # Already imported
        
        skey_file_path = "payment.skey"
        vkey_file_path = "payment.vkey"

        # Check if skey file exists, otherwise prompt or generate
        if os.path.exists(skey_file_path):
            print(f"Found existing signing key file: {skey_file_path}")
            # Optionally, could load and display the address here as a check
            # temp_skey = PaymentSigningKey.load(skey_file_path)
            # temp_vkey = PaymentVerificationKey.from_signing_key(temp_skey)
            # temp_addr = Address(temp_vkey.hash(), network=Network.TESTNET)
            # print(f"    Associated address: {temp_addr}")
        else:
            print(f"Signing key file '{skey_file_path}' not found.")
            generate_new = input("❓ Would you like to generate a new key pair (payment.skey, payment.vkey)? (y/N): ").strip().lower()
            if generate_new == 'y':
                new_skey = PaymentSigningKey.generate()
                new_skey.save(skey_file_path)
                new_vkey = PaymentVerificationKey.from_signing_key(new_skey)
                new_vkey.save(vkey_file_path)
                new_addr = Address(new_vkey.hash(), network=Network.TESTNET)
                print(f"🔑 New key pair generated and saved!")
                print(f"   Signing key: {skey_file_path}")
                print(f"   Verification key: {vkey_file_path}")
                print(f"   Testnet Address: {new_addr}")
                print("💡 FUND THIS ADDRESS with test ADA from a faucet before proceeding with payment.")
            else:
                print("❌ Cannot proceed without a signing key. Please create 'payment.skey' or allow generation.")
                raise FileNotFoundError(f"'{skey_file_path}' not found and not generated.")

        user_blockfrost_id = input("❄️ Enter your Blockfrost Project ID for Preprod/Testnet (required for payment): ").strip() or None
        if not user_blockfrost_id:
            print("⚠️  No Blockfrost Project ID provided. Payment will likely fail.")
            # raise ValueError("Blockfrost Project ID is required to make a payment.")

        print(f"\n🔧 Using signing key from '{skey_file_path}'.")
        print(f"❄️ Blockfrost ID: {user_blockfrost_id if user_blockfrost_id else 'Not provided (payment will fail)'}")
        
        return WalletConfig(
            signing_key_file=skey_file_path, # Pass the file path correctly
            network=Network.TESTNET, # Ensure this matches your wallet's network
            blockfrost_project_id=user_blockfrost_id
        )
    else:
        raise Exception("PyCardano not available")

def main():
    """
    Main function demonstrating advanced Masumi client
    """
    if not PYCARDANO_AVAILABLE:
        print("❌ PyCardano library required!")
        print("💡 Install with: pip install pycardano requests python-dotenv")
        return
    
    if len(sys.argv) < 2:
        print("Usage: python client_pycardano.py '<message>'")
        print("Example: python client_pycardano.py 'Hello Echo Agent!'")
        return
    
    message = sys.argv[1]
    
    print("🔊 Advanced Echo Agent Client - PyCardano")
    print("=" * 60)
    print("💡 This demonstrates proper Masumi integration")
    print("💡 No Masumi payment node required on client side!")
    print("💡 Uses PyCardano for blockchain interactions")
    print("=" * 60)
    
    try:
        # Create wallet configuration
        wallet_config = create_example_wallet_config()
        wallet_client = PyCardanoWalletClient(wallet_config)
        
        print(f"\n📍 Your wallet address: {wallet_client.get_address()}")

        # Check balance first
        total_lovelace, utxos = wallet_client.check_balance()

        if total_lovelace is None: # Indicates an error during balance check
            print("\nAborting due to issues fetching wallet balance.")
            return
        
        if not wallet_config.blockfrost_project_id:
            print("⚠️  WARNING: No Blockfrost Project ID provided.")
            print("   Real blockchain transactions (balance check, payment) will likely fail.")
            print("   The script will attempt to start the job but may not complete payment.")
        
        # Create agent client
        agent_client = MasumiAgentClientAdvanced("http://localhost:8000", wallet_client)
        
        # Step 1: Start job (this will work if agent is running)
        try:
            print("\n🔄 Starting job with the agent...")
            job_info = agent_client.start_job(message)
            job_id = job_info["blockchainIdentifier"] # Make sure your agent returns this key
            seller_wallet = job_info["sellerWalletAddress"]
            ada_amount = None
            for amount_detail in job_info["amounts"]:
                if amount_detail["unit"] == "lovelace":
                    ada_amount = int(amount_detail["amount"])
                    break
            
            if not all([job_id, seller_wallet, ada_amount is not None]):
                print("❌ Agent response missing critical payment information (blockchainIdentifier, sellerWalletAddress, or lovelace amount).")
                print(f"📄 Agent response: {json.dumps(job_info, indent=2)}")
                return

            print(f"\n✅ Job '{job_id}' started successfully!")
            print(f"💰 Required payment: {ada_amount} lovelace to {seller_wallet}")

            if not wallet_config.blockfrost_project_id:
                print("\n⚠️  Skipping actual payment due to missing Blockfrost ID.")
                print("💡 To complete the payment, provide a Blockfrost Project ID when starting the script.")
            else:
                # Step 2: Make direct blockchain payment
                print("\n💳 Attempting to make blockchain payment...")
                tx_hash = agent_client.make_payment(job_info)
                print(f"🔗 Payment transaction hash: {tx_hash}")
            
                # Step 3: Wait for completion (optional, can be long)
                # print("\n⏳ Waiting for job completion (this might take a few minutes)...")
                # final_result = agent_client.wait_for_completion(job_id)
                # if final_result and final_result.get("result"):
                # print(f"\n🎯 Final Result: {final_result['result']}")
                # else:
                # print("\n❌ No final result obtained or job failed.")
                print("\n✅ Payment submitted. You can manually check the job status later or implement polling.")

        except requests.RequestException as e:
            print(f"❌ Could not connect to agent: {e}")
            print("💡 Make sure the echo agent is running at http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 