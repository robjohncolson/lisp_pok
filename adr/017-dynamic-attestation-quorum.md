# 017. Dynamic Attestation Quorum

- **Status:** Accepted
- **Date:** 2024-12-19

## Context

The current consensus mechanism requires a fixed number of attestations (e.g., 3) to finalize a block. This approach has several limitations:

1. **Network brittleness:** If fewer than 3 peers are online, no block can ever be finalized, making the network non-functional in low-participation scenarios.

2. **Poor scalability:** If the network grows to 45 peers, requiring only 3 attestations might be too low to represent meaningful consensus, potentially compromising security.

3. **Lack of adaptability:** The fixed threshold doesn't adjust to the actual network participation, leading to either over-restrictive or under-restrictive consensus requirements.

## Decision

We will implement a "Dynamic Quorum" rule where the number of required attestations is calculated based on the number of currently active peers.

### Implementation Details

1. **Quorum Formula:** 30% of online peers, with a minimum of 3 and a maximum of 7 attestations required.

2. **Code Changes:** The `_checkForBlockFinalization` method in the `BlockchainService` will be updated to:
   - Calculate the required number of attestations dynamically before checking the vote tally
   - Use `this.state.connectedPeers.length` to determine the number of online peers
   - Apply the formula: `Math.ceil(connectedPeers * 0.3)` with bounds `[3, 7]`

3. **Calculation Examples:**
   - 3 peers: `Math.ceil(3 * 0.3) = 1` → **3** (minimum enforced)
   - 10 peers: `Math.ceil(10 * 0.3) = 3` → **3**
   - 20 peers: `Math.ceil(20 * 0.3) = 6` → **6**
   - 30+ peers: `Math.ceil(30 * 0.3) = 9` → **7** (maximum enforced)

## Consequences

### Positive Outcomes

- **Improved network liveness:** The network becomes more resilient and can continue to function with fewer online users, preventing complete network halt in low-participation scenarios.

- **Automatic scaling:** The consensus mechanism automatically adapts to network size without requiring manual configuration changes, making the system more maintainable.

- **Balanced security:** The system maintains reasonable security thresholds while allowing for network growth and varying participation levels.

### Trade-offs

- **Variable security:** The security level of a block is now dependent on how many peers were online when it was finalized. Blocks finalized during low-participation periods will have lower security guarantees.

- **Complexity:** The consensus logic becomes slightly more complex as it now needs to calculate dynamic thresholds rather than using a fixed value.

### Acceptable Risk

The variable security trade-off is acceptable for our use case, as the educational nature of the AP Statistics learning platform prioritizes network availability and user experience over maximum security. The bounded approach (minimum 3, maximum 7) ensures we maintain reasonable security baselines while preventing excessive requirements in large networks. 