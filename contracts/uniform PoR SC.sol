// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ProofOfReputation
 * @dev Implements a Proof-of-Reputation consensus mechanism where clients earn reputation based on various factors.
 */
contract ProofOfReputation {

    /**
     * @dev Represents a client in the system.
     */
    struct Client {
        uint256 reputationScore;       // Current reputation score
        uint256 historicalPerformance; // Historical performance metric
        uint256 trustworthiness;       // Trustworthiness metric
        uint256 contribution;          // Contribution metric
        uint256 peerReviews;           // Peer reviews metric
        uint256 validationAccuracy;    // Validation accuracy metric
        bool isValidator;              // Indicates if the client is currently a validator
        bool jobSubmitted;             // Indicates if the client has submitted a job in the current round
    }

    // Mapping from client address to Client struct
    mapping(address => Client) public clients;

    // Array of all client addresses
    address[] public clientAddresses;

    // Address of the current validator
    address public currentValidator;

    // Total reputation in the system
    uint256 public totalReputation;

    // Weights for the reputation factors (in percentages)
    // uint256 public weightH = 15;  // 15% for Historical Performance
    // uint256 public weightT = 25;  // 25% for Trustworthiness
    // uint256 public weightC = 20;  // 20% for Contribution
    // uint256 public weightP = 15;  // 15% for Peer Reviews
    // uint256 public weightV = 25;  // 25% for Validation Accuracy
       
    uint256 public weightH = 20;  // 20% for Historical Performance
    uint256 public weightT = 20;  // 20% for Trustworthiness
    uint256 public weightC = 20;  // 20% for Contribution
    uint256 public weightP = 20;  // 20% for Peer Reviews
    uint256 public weightV = 20;  // 20% for Validation Accuracy

    // Penalty for failed validation (reputation points)
    uint256 public penalty = 10;

    // Reward for the validator after successful validation (reputation points)
    // uint256 public validatorReward = 10;
    uint256 public validatorReward = 2;

    // Events for logging various actions
    event ClientAdded(address indexed client);
    event ValidatorSelected(address indexed validator);
    event JobSubmitted(address indexed client, string result);
    event JobValidated(address indexed validator, address indexed client, bool success);
    event ClientScoreUpdated(address indexed client, uint256 newScore);
    event ValidatorRewarded(address indexed validator, uint256 reward);
    event ValidatorPenalized(address indexed validator, uint256 penalty);
    
    // New Events for Client Rewards and Penalties
    event ClientRewarded(address indexed client, uint256 reward);
    event ClientPenalized(address indexed client, uint256 penalty);

    /**
     * @dev Adds a new client to the system with initialized parameters.
     * @param _client The address of the client.
     * @param _initialReputation The initial reputation score of the client.
     * @param _historicalPerformance The initial historical performance metric.
     * @param _trustworthiness The initial trustworthiness metric.
     * @param _contribution The initial contribution metric.
     * @param _peerReviews The initial peer reviews metric.
     * @param _validationAccuracy The initial validation accuracy metric.
     */
    function addClient(
        address _client,
        uint256 _initialReputation,
        uint256 _historicalPerformance,
        uint256 _trustworthiness,
        uint256 _contribution,
        uint256 _peerReviews,
        uint256 _validationAccuracy
    ) public {
        require(_client != address(0), "Invalid client address");
        require(clients[_client].reputationScore == 0, "Client already exists");
        require(_initialReputation > 0, "Initial reputation must be greater than zero");

        // Initialize the Client struct
        clients[_client] = Client({
            reputationScore: _initialReputation,
            historicalPerformance: _historicalPerformance,
            trustworthiness: _trustworthiness,
            contribution: _contribution,
            peerReviews: _peerReviews,
            validationAccuracy: _validationAccuracy,
            isValidator: false,
            jobSubmitted: false
        });

        // Add the client address to the array
        clientAddresses.push(_client);

        // Update the total reputation
        totalReputation += _initialReputation;

        emit ClientAdded(_client);

        // Select a validator after adding a new client
        selectValidator();
    }

    /**
     * @dev Calculates and applies a reputation reward to a client based on their performance metrics.
     * @param _client The address of the client to reward.
     */
    function calculateReputationReward(address _client) internal {
        Client storage client = clients[_client];
        require(client.reputationScore > 0, "Client does not exist or has zero reputation");

        // Calculate the new reputation based on weighted metrics
        uint256 newReputation = (
            (weightH * client.historicalPerformance) +
            (weightT * client.trustworthiness) +
            (weightC * client.contribution) +
            (weightP * client.peerReviews) +
            (weightV * client.validationAccuracy)
        ) / 100;

        // Update the client's reputation score
        client.reputationScore += newReputation;
        totalReputation += newReputation;

        emit ClientScoreUpdated(_client, client.reputationScore);
        emit ClientRewarded(_client, newReputation);
    }

    /**
     * @dev Allows a client to submit a job.
     * @param result A string representing the job's result or description.
     */
    function submitJob(string memory result) public {
        Client storage client = clients[msg.sender];
        require(client.reputationScore > 0, "Client does not exist");
        require(!client.jobSubmitted, "Job already submitted for this round");

        // Mark that the client has submitted a job
        client.jobSubmitted = true;

        emit JobSubmitted(msg.sender, result);
    }

    /**
     * @dev Allows the current validator to validate all submitted jobs.
     * @param successes An array of boolean values indicating the success or failure of each client's job.
     *        The order should correspond to the `clientAddresses` array.
     */
    function validateAllJobs(bool[] memory successes) public {
        require(msg.sender == currentValidator, "Only the current validator can validate jobs");
        require(successes.length == clientAddresses.length, "Input array length mismatch");

        // Iterate through all clients to validate their jobs
        for (uint256 i = 0; i < clientAddresses.length; i++) {
            address clientAddr = clientAddresses[i];
            Client storage client = clients[clientAddr];

            if (client.jobSubmitted) {
                // Reset job submission status
                client.jobSubmitted = false;

                if (successes[i]) {
                    // If the job is successful, update client factors and reward reputation
                    updateClientFactors(clientAddr);
                    emit JobValidated(msg.sender, clientAddr, true);
                } else {
                    // If the job fails, apply a penalty to the client's reputation
                    applyPenalty(clientAddr);
                    emit JobValidated(msg.sender, clientAddr, false);
                }
            }
        }

        // Reward the validator for successfully validating jobs
        rewardValidator();

        // Select a new validator based on updated reputation scores
        selectValidator();
    }

    /**
     * @dev Applies a penalty to a client's reputation score for failed job validation.
     * @param _client The address of the client to penalize.
     */
    function applyPenalty(address _client) internal {
        Client storage client = clients[_client];
        require(client.reputationScore > 0, "Client does not exist or has zero reputation");

        uint256 penaltyAmount = penalty;

        if (client.reputationScore <= penalty) {
            // If the client's reputation is less than or equal to the penalty, set it to zero
            penaltyAmount = client.reputationScore;
            client.reputationScore = 0;
            totalReputation -= penaltyAmount;
        } else {
            // Otherwise, subtract the penalty from the reputation score
            client.reputationScore -= penaltyAmount;
            totalReputation -= penaltyAmount;
        }

        emit ClientScoreUpdated(_client, client.reputationScore);
        emit ClientPenalized(_client, penaltyAmount);
    }

    /**
     * @dev Updates a client's performance metrics after a successful job validation.
     * @param _client The address of the client to update.
     */
    function updateClientFactors(address _client) internal {
        Client storage client = clients[_client];
        require(client.reputationScore > 0, "Client does not exist or has zero reputation");

        // Increment performance metrics (example logic; adjust as needed)
        client.historicalPerformance += 1;
        client.trustworthiness += 1;
        client.contribution += 1;
        client.peerReviews += 1;
        client.validationAccuracy += 1;

        // Calculate and apply the reputation reward based on updated metrics
        calculateReputationReward(_client);
    }

    /**
     * @dev Rewards the current validator for validating jobs.
     */
    function rewardValidator() internal {
        require(currentValidator != address(0), "No validator selected");

        Client storage validator = clients[currentValidator];
        require(validator.reputationScore > 0, "Validator does not exist or has zero reputation");

        // Apply the reward to the validator's reputation score
        validator.reputationScore += validatorReward;
        totalReputation += validatorReward;

        emit ValidatorRewarded(currentValidator, validatorReward);
    }

    /**
     * @dev Selects the client with the highest reputation score as the new validator.
     *      In case of a tie, the first encountered client with the maximum score is selected.
     */
    function selectValidator() internal {
        uint256 maxReputation = 0;
        address selectedValidator = address(0);

        // Iterate through all clients to find the one with the highest reputation score
        for (uint256 i = 0; i < clientAddresses.length; i++) {
            address clientAddr = clientAddresses[i];
            uint256 reputation = clients[clientAddr].reputationScore;

            if (reputation > maxReputation) {
                maxReputation = reputation;
                selectedValidator = clientAddr;
            }
        }

        require(selectedValidator != address(0), "Validator selection failed");

        // Update the current validator
        currentValidator = selectedValidator;

        // Update the `isValidator` flag for all clients
        for (uint256 i = 0; i < clientAddresses.length; i++) {
            address clientAddr = clientAddresses[i];
            clients[clientAddr].isValidator = (clientAddr == currentValidator);
        }

        emit ValidatorSelected(selectedValidator);
    }

    /**
     * @dev Returns the address of the current validator.
     * @return The address of the current validator.
     */
    function getCurrentValidator() external view returns (address) {
        return currentValidator;
    }

    /**
     * @dev Returns the reputation score of a specific client.
     * @param _client The address of the client.
     * @return The reputation score of the client.
     */
    function getReputationScore(address _client) external view returns (uint256) {
        return clients[_client].reputationScore;
    }

    /**
     * @dev Returns the total reputation score in the system.
     * @return The total reputation score.
     */
    function getTotalReputation() external view returns (uint256) {
        return totalReputation;
    }

    /**
     * @dev Returns the list of all client addresses.
     * @return An array of client addresses.
     */
    function getAllClients() external view returns (address[] memory) {
        return clientAddresses;
    }
}
