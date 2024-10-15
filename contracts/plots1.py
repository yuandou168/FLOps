# Import necessary libraries
from web3 import Web3
import json
import solcx
import random
import matplotlib.pyplot as plt

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

# Initialize data storage
reputation_history = {address: [] for address in w3.eth.accounts}  # Adjust for the number of clients
success_history = []
failure_history = []
submission_success_counts = {address: 0 for address in w3.eth.accounts}
submission_failure_counts = {address: 0 for address in w3.eth.accounts}
validation_success_counts = {address: 0 for address in w3.eth.accounts}
validation_failure_counts = {address: 0 for address in w3.eth.accounts}

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
        ).transact({'from': w3.eth.default_account})
        log_gas_usage(tx_hash, f"Adding client {client_address}")
    except Exception as e:
        print(f"Error adding client {client_address}: {str(e)}")

# Submit a job
def submit_job(client_address, job_result):
    try:
        tx_hash = deployed_contract.functions.submitJob(job_result).transact({'from': client_address})
        log_gas_usage(tx_hash, f"Client {client_address} submitting job")
        submission_success_counts[client_address] += 1
    except Exception as e:
        print(f"Error submitting job by client {client_address}: {str(e)}")
        submission_failure_counts[client_address] += 1

# Validate all jobs, specifying success or failure for each client
def validate_all_jobs(validator_address, successes):
    try:
        tx_hash = deployed_contract.functions.validateAllJobs(successes).transact({'from': validator_address})
        log_gas_usage(tx_hash, "Validating all jobs")
        for i, success in enumerate(successes):
            client_address = w3.eth.accounts[i]
            if success:
                validation_success_counts[validator_address] += 1
            else:
                validation_failure_counts[validator_address] += 1
    except Exception as e:
        print(f"Error validating jobs by validator {validator_address}: {str(e)}")
        validation_failure_counts[validator_address] += 1

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
    
    accounts = w3.eth.accounts[:K]  # Use the first K Ganache accounts

    # Add K clients with initialized parameters
    for i in range(K):
        initial_reputation = random.randint(50, 100)
        historical_performance = random.randint(0, 10)
        trustworthiness = random.randint(0, 10)
        contribution = random.randint(0, 10)
        peer_reviews = random.randint(0, 10)
        validation_accuracy = random.randint(0, 10)

        add_client(
            accounts[i], 
            initial_reputation,
            historical_performance,
            trustworthiness,
            contribution,
            peer_reviews,
            validation_accuracy
        )
        print()
    
    # Run N rounds of job submissions and validations
    for round_num in range(1, N + 1):
        print(f"\n--- Round {round_num} ---")
        
        # Each client submits a job
        for i in range(K):
            submit_job(accounts[i], f"Job {round_num} from Client {i + 1}")
        
        # Randomly decide if each job is successful or not
        successes = [random.choice([True, False]) for _ in range(K)]
        success_count = sum(successes)
        failure_count = K - success_count

        success_history.append(success_count)
        failure_history.append(failure_count)

        # Validator validates all jobs
        current_validator = deployed_contract.functions.getCurrentValidator().call()
        print(f"Current Validator: {current_validator}")
        validate_all_jobs(current_validator, successes)
        
        # Store the updated reputations for each client
        for i in range(K):
            reputation = get_reputation(accounts[i])
            reputation_history[accounts[i]].append(reputation)

# Example usage: Test with 5 clients over 10 rounds
run_test(K=5, N=10)

# Plot the results
def plot_results():
    # Plot reputation history
    plt.figure(figsize=(14, 7))
    for address, reputations in reputation_history.items():
        if reputations:  # Only plot if there is data
            plt.plot(reputations, label=address[:10] + "...")  # Truncate the address for readability
    
    plt.title('Reputation Over Time', fontsize=16)
    plt.xlabel('Round', fontsize=14)
    plt.ylabel('Reputation', fontsize=14)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Plot success/failure history
    plt.figure(figsize=(10, 5))
    plt.plot(success_history, label='Successes', marker='o', color='green', linestyle='--')
    plt.plot(failure_history, label='Failures', marker='x', color='red', linestyle='-')
    plt.title('Validation Outcomes Over Time', fontsize=16)
    plt.xlabel('Round', fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Plot submission success rate
    plt.figure(figsize=(10, 5))
    for address in submission_success_counts.keys():
        total_submissions = submission_success_counts[address] + submission_failure_counts[address]
        if total_submissions > 0:
            success_rate = submission_success_counts[address] / total_submissions
            plt.bar(address[:10], success_rate, color='blue', alpha=0.7)
    
    plt.title('Job Submission Success Rate by Client', fontsize=16)
    plt.xlabel('Client', fontsize=14)
    plt.ylabel('Success Rate', fontsize=14)
    plt.ylim(0, 1)
    plt.grid(True, axis='y')
    plt.tight_layout()
    plt.show()

    # Plot validation success rate
    plt.figure(figsize=(10, 5))
    for address in validation_success_counts.keys():
        total_validations = validation_success_counts[address] + validation_failure_counts[address]
        if total_validations > 0:
            success_rate = validation_success_counts[address] / total_validations
            plt.bar(address[:10], success_rate, color='green', alpha=0.7)
    
    plt.title('Validation Success Rate by Validator', fontsize=16)
    plt.xlabel('Validator', fontsize=14)
    plt.ylabel('Success Rate', fontsize=14)
   
