# Import necessary libraries
from web3 import Web3
import json
import solcx
import random

# Connect to the local Ethereum network (Ganache)
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Check if connection is successful
if not w3.is_connected():
    raise Exception("Failed to connect to the Ethereum network")

# Set the default account (deployer)
w3.eth.default_account = w3.eth.accounts[0]

# Compile the contract using solcx
solcx.install_solc('0.8.0')
solcx.set_solc_version('0.8.0')

# Path to your Solidity contract
contract_path = "./ProofOfReputation.sol"  # Update this path to your contract

# Compile the Solidity contract
with open(contract_path, "r") as file:
    contract_source_code = file.read()

compiled_sol = solcx.compile_standard({
    "language": "Solidity",
    "sources": {
        "ProofOfReputation.sol": {
            "content": contract_source_code
        }
    },
    "settings": {
        "outputSelection": {
            "*": {
                "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
            }
        }
    }
})

# Extract ABI and bytecode
abi = compiled_sol['contracts']['ProofOfReputation.sol']['ProofOfReputation']['abi']
bytecode = compiled_sol['contracts']['ProofOfReputation.sol']['ProofOfReputation']['evm']['bytecode']['object']

# Deploy the contract
ProofOfReputation = w3.eth.contract(abi=abi, bytecode=bytecode)

# Deploy the contract and get the transaction hash
tx_hash = ProofOfReputation.constructor().transact()
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
contract_address = tx_receipt.contractAddress
print(f"Contract deployed at address: {contract_address}")

# Get the deployed contract instance
deployed_contract = w3.eth.contract(address=contract_address, abi=abi)

# Function to log gas used
def log_gas_usage(tx_hash, action):
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    print(f"Gas used for {action}: {receipt.gasUsed}")

# Add a new client with initialized parameters
def add_client(client_address, initial_reputation, historical_performance, trustworthiness, contribution, peer_reviews, validation_accuracy):
    try:
        tx_hash = deployed_contract.functions.addClient(
            client_address,
            initial_reputation,
            historical_performance,
            trustworthiness,
            contribution,
            peer_reviews,
            validation_accuracy
        ).transact()
        # log_gas_usage(tx_hash, f"Adding client {client_address}")
    except Exception as e:
        print(f"Error adding client {client_address}: {str(e)}")

# Submit a job
def submit_job(client_address, job_result):
    try:
        tx_hash = deployed_contract.functions.submitJob(job_result).transact({'from': client_address})
        # log_gas_usage(tx_hash, f"Client {client_address} submitting job")
    except Exception as e:
        print(f"Error submitting job by client {client_address}: {str(e)}")

# Validate all jobs, specifying success or failure for each client
def validate_all_jobs(validator_address, successes):
    try:
        tx_hash = deployed_contract.functions.validateAllJobs(successes).transact({'from': validator_address})
        log_gas_usage(tx_hash, "Validating all jobs")
    except Exception as e:
        print(f"Error validating jobs by validator {validator_address}: {str(e)}")

# Fetching updated reputations
def get_reputation(client_address):
    try:
        reputation = deployed_contract.functions.getReputationScore(client_address).call()
        print(f"Reputation of client {client_address}: {reputation}")
        return reputation
    except Exception as e:
        print(f"Error fetching reputation for client {client_address}: {str(e)}")

# Run the test with K clients and N rounds
def run_test(K, N):
    print(f"Running test with {K} clients and {N} rounds\n")
    
    # Add K clients with initialized parameters
    for i in range(1, K + 1):
        initial_reputation = random.randint(30, 50)
        historical_performance = random.randint(0, 10)
        trustworthiness = random.randint(0, 10)
        contribution = random.randint(0, 10)
        peer_reviews = random.randint(0, 10)
        validation_accuracy = random.randint(0, 10)

        add_client(
            w3.eth.accounts[i], 
            initial_reputation,
            historical_performance,
            trustworthiness,
            contribution,
            peer_reviews,
            validation_accuracy
        )
        print(f"Initialized reputation of client: {w3.eth.accounts[i]} is {initial_reputation}")
    
    # Run N rounds of job submissions and validations
    for round_num in range(1, N + 1):
        print(f"\n--- Round {round_num} ---")
        
        # Each client submits a job
        for i in range(1, K + 1):
            submit_job(w3.eth.accounts[i], f"Job {round_num} from Client {i}")
        
        # Randomly decide if each job is successful or not
        successes = [random.choice([True, False]) for _ in range(K)]

        # Validator validates all jobs
        current_validator = deployed_contract.functions.getCurrentValidator().call()
        print(f"Current Validator: {current_validator}")
        validate_all_jobs(current_validator, successes)
        
        # Display the updated reputations
        for i in range(1, K + 1):
            get_reputation(w3.eth.accounts[i])

# Example usage: Test with K clients over N rounds
run_test(K=10, N=6)
