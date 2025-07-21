# ADR-016: Priority Transaction Reward for Miners

## Status

Proposed

## Context

Currently, there is no direct, in-game reward for a student who successfully mines a block by solving a puzzle and gathering attestations. We need a mechanism to incentivize this crucial network activity.

The existing system allows students to:
- Solve academic puzzles to create attestations
- Mine blocks by gathering sufficient attestations and solving cryptographic challenges
- Submit their completed work as transactions

However, there is no immediate benefit for the student who performs the mining work, which may reduce participation in this critical network function.

## Decision

We will implement a "Priority Transaction" reward system with the following components:

1. **Transaction Interface Update**: The `Transaction` interface will be updated with a new optional boolean field: `isPriority?: boolean;`.

2. **Miner Tracking**: The `BlockchainService` will track the public key of the last successful block miner.

3. **Priority Transaction Creation**: When creating a new `ACTIVITY_COMPLETE` transaction, the `createTransaction` method will check if the transaction's author is the last successful miner. If they are, it will add `isPriority: true` to the transaction's payload and then clear the "last miner" flag, making the reward a one-time bonus.

4. **Priority Block Assembly**: The `proposeBlock` method will be updated. When assembling transactions for a new block, it must first include all pending transactions where `payload.isPriority === true`, before including other transactions.

This creates a cycle where:
- Student A mines a block successfully
- Student A's next activity completion gets priority processing
- Student A's priority transaction gets included first in the next block
- The system resets, ready to reward the next successful miner

## Consequences

### Positive

- **Direct Mining Incentive**: Creates a direct and strategic incentive for mining, rewarding participants with faster confirmation of their own work.
- **Economic Layer**: Adds a new, interesting economic layer to the system without using a token or "coin."
- **Network Activity**: Encourages continued participation in the mining process, which is essential for network security and progress.
- **Fair Distribution**: The one-time nature ensures rewards are distributed among different participants rather than concentrated.

### Negative

- **Implementation Complexity**: Increases the complexity of the `createTransaction` and `proposeBlock` methods.
- **State Management**: Requires additional state tracking for the last successful miner.
- **Testing Overhead**: Will require comprehensive testing of the priority logic and edge cases.

### Neutral

- **Transaction Processing**: Priority transactions will be processed first, which may slightly delay non-priority transactions but should not significantly impact overall system performance. 