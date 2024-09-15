// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ProofOfReputation {

    struct Client {
        uint256 reputationScore;
        uint256 historicalPerformance;
        uint256 trustworthiness;
        uint256 contribution;
        uint256 peerReviews;
        uint256 validationAccuracy;
        bool isValidator;
        bool jobSubmitted;
    }

    mapping(address => Client) public clients;
    address[] public clientAddresses;
    address public currentValidator;
    uint256 public totalReputation;

    // Weights for the reputation factors
    uint256 public weightH = 15;  // 15% for Historical Performance
    uint256 public weightT = 25;  // 25% for Trustworthiness
    uint256 public weightC = 20;  // 20% for Contribution
    uint256 public weightP = 20;  // 20% for Peer Reviews
    uint256 public weightV = 20;  // 20% for Validation Accuracy

    // Penalty for failed validation
    uint256 public penalty = 10;  // 10 reputation points

    // Events for logging
    event ClientAdded(address client);
    event ValidatorSelected(address validator);
    event JobSubmitted(address client, string result);
    event JobValidated(address validator, address client, bool success);
    event ClientScoreUpdated(address client, uint256 newScore);
    event ValidatorRewarded(address validator, uint256 reward);
    event ValidatorPenalized(address validator, uint256 penalty);

    /**
     * @dev Add a new client with initialized parameters.
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
        require(clients[_client].reputationScore == 0, "Client already exists");

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

        clientAddresses.push(_client);
        totalReputation += _initialReputation;

        emit ClientAdded(_client);
        selectValidator();
    }

    /**
     * @dev Update the reputation score based on updated factors.
     */
    function calculateReputationReward(address _client) internal {
        Client storage client = clients[_client];

        uint256 newReputation = (
            weightH * client.historicalPerformance +
            weightT * client.trustworthiness +
            weightC * client.contribution +
            weightP * client.peerReviews +
            weightV * client.validationAccuracy
        ) / 100;

        // Apply the reward to the client's reputation score
        client.reputationScore += newReputation;
        totalReputation += newReputation;

        emit ClientScoreUpdated(_client, client.reputationScore);
    }

    /**
     * @dev Function to submit a job by a client.
     */
    function submitJob(string memory result) public {
        require(clients[msg.sender].reputationScore != 0, "Client does not exist");
        require(!clients[msg.sender].jobSubmitted, "Job already submitted");

        clients[msg.sender].jobSubmitted = true;

        emit JobSubmitted(msg.sender, result);
    }

    /**
     * @dev Function to validate all jobs by the current validator.
     */
    function validateAllJobs(bool[] memory successes) public {
        require(msg.sender == currentValidator, "Only the current validator can validate jobs");
        require(successes.length == clientAddresses.length, "Invalid input length");

        // Iterate through all clients and validate jobs
        for (uint256 i = 0; i < clientAddresses.length; i++) {
            address clientAddr = clientAddresses[i];
            if (clients[clientAddr].jobSubmitted) {
                clients[clientAddr].jobSubmitted = false;

                if (successes[i]) {
                    // Update client factors based on job validation
                    updateClientFactors(clientAddr);
                    emit JobValidated(msg.sender, clientAddr, true);
                } else {
                    // Apply penalty if validation fails
                    applyPenalty(clientAddr);
                    emit JobValidated(msg.sender, clientAddr, false);
                }
            }
        }

        // Reward the validator after successful validation
        rewardValidator();

        // Select a new validator based on updated reputation scores
        selectValidator();
    }

    /**
     * @dev Apply a penalty to the client's reputation score on failed validation.
     */
    function applyPenalty(address _client) internal {
        if (clients[_client].reputationScore > penalty) {
            clients[_client].reputationScore -= penalty;
            totalReputation -= penalty;
        } else {
            totalReputation -= clients[_client].reputationScore;
            clients[_client].reputationScore = 0;
        }

        emit ClientScoreUpdated(_client, clients[_client].reputationScore);
    }

    /**
     * @dev Update the client's factors after validation.
     */
    function updateClientFactors(address _client) internal {
        // Update the client's factors
        clients[_client].historicalPerformance += 1;  // Example increment
        clients[_client].trustworthiness += 1;        // Example increment
        clients[_client].contribution += 1;           // Example increment
        clients[_client].peerReviews += 1;            // Example increment
        clients[_client].validationAccuracy += 1;     // Example increment

        // After updating the factors, calculate the reputation reward
        calculateReputationReward(_client);
    }

    /**
     * @dev Internal function to reward the current validator.
     */
    function rewardValidator() internal {
        uint256 reward = 3;  // Example reward amount
        clients[currentValidator].reputationScore += reward;
        totalReputation += reward;

        emit ValidatorRewarded(currentValidator, reward);
    }

    /**
     * @dev Internal function to select the validator with the highest reputation score.
     */
    function selectValidator() internal {
        uint256 maxReputation = 0;
        address selectedValidator = address(0);

        for (uint256 i = 0; i < clientAddresses.length; i++) {
            address clientAddr = clientAddresses[i];
            uint256 reputation = clients[clientAddr].reputationScore;

            if (reputation > maxReputation) {
                maxReputation = reputation;
                selectedValidator = clientAddr;
            }
        }

        require(selectedValidator != address(0), "Validator selection failed");

        currentValidator = selectedValidator;

        for (uint256 i = 0; i < clientAddresses.length; i++) {
            clients[clientAddresses[i]].isValidator = (clientAddresses[i] == currentValidator);
        }

        emit ValidatorSelected(selectedValidator);
    }

    /**
     * @dev External function to get the current validator's address.
     * @return The address of the current validator.
     */
    function getCurrentValidator() external view returns (address) {
        return currentValidator;
    }

    /**
     * @dev External function to get the reputation score of a client.
     * @param _client The address of the client.
     * @return The reputation score of the client.
     */
    function getReputationScore(address _client) external view returns (uint256) {
        return clients[_client].reputationScore;
    }

    /**
     * @dev External function to get the total reputation in the system.
     * @return The total reputation score.
     */
    function getTotalReputation() external view returns (uint256) {
        return totalReputation;
    }
}
