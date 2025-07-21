# ADR-026: Granular Progress Transactions for PoK

**Date:** 2025-01-27  
**Status:** Accepted  
**Context:** V2 Development Phase - Blockchain-Powered Student Experience  

## Context

Building on [ADR-012: Social Consensus and Proof of Knowledge](./012-social-consensus-and-proof-of-knowledge.md), we need a transaction structure that captures student progress on individual questions while supporting the emergent consensus model. The current transaction system handles general blockchain operations but lacks the granular detail needed for tracking per-question completions across different question types.

The educational content, as outlined in [ADR-025: Unified Granular JSON Schema](./025-unified-granular-json-schema-for-curriculum-and-questions.md), includes two primary question types:
- **Multiple Choice Questions (MCQs)**: Options-based with deterministic correct answers
- **Free Response Questions (FRQs)**: Open-ended with rubric-based scoring

For the Proof of Knowledge system to function effectively, we need transactions that:
1. Capture student responses without immediately revealing correctness
2. Support social consensus verification as described in ADR-012
3. Enable efficient batching for performance
4. Maintain cryptographic integrity through signatures

## Decision

We will implement a **Granular Progress Transaction** system with the following structure:

### Core Transaction Interface

```typescript
interface CompletionTransaction {
  type: 'completion';
  questionId: string;
  answerHash?: string;     // For MCQs - hashed selected option
  answerText?: string;     // For FRQs - raw text response
  userPubKey: string;
  timestamp: number;
  signature: string;
}
```

### Question Type Handling

**Multiple Choice Questions (MCQs)**:
- Use `answerHash` field containing SHA-256 hash of selected option key
- Hash matches against known option keys during consensus verification
- Prevents immediate answer revelation while enabling verification

**Free Response Questions (FRQs)**:
- Use `answerText` field containing raw student response
- Enable rubric-based peer assessment during consensus phase
- Support structured scoring as defined in ADR-025

### Emergent Consensus Integration

Following ADR-012's social consensus model:
1. **No Immediate Correctness**: Transactions contain responses without correctness flags
2. **Peer Verification**: Other students verify responses during attestation phase
3. **Quorum-Based Finality**: Transactions become final after sufficient peer attestations
4. **Distributed Validation**: No centralized answer key required

### Batching for Efficiency

To optimize network performance and reduce transaction overhead:
- **Batch Size**: 5-10 completion transactions per batch
- **Atomic Processing**: Entire batch succeeds or fails together
- **Signature Optimization**: Single signature covers entire batch
- **Network Efficiency**: Reduces P2P message volume

### Implementation Components

1. **Transaction Creation**: `createCompletionTransaction()` with crypto signing
2. **Batch Validator**: `validateTransactionBatch()` for integrity checks
3. **Type Guards**: Runtime validation for MCQ vs FRQ formats
4. **Local Storage**: In-memory array preparation for blockchain integration

## Technical Specifications

### Validation Rules

**MCQ Transactions**:
- Must include `answerHash` field
- Hash must be valid SHA-256 (64 hex characters)
- `answerText` field must be undefined

**FRQ Transactions**:
- Must include `answerText` field
- Text must be non-empty string
- `answerHash` field must be undefined

**Universal Requirements**:
- Valid `questionId` format
- Valid secp256k1 signature
- Timestamp within reasonable bounds
- User public key matches signature

### Batch Processing

```typescript
interface TransactionBatch {
  transactions: CompletionTransaction[];
  batchId: string;
  userPubKey: string;
  batchSignature: string;
  timestamp: number;
}
```

## Implementation Strategy

### Phase 1: Core Transaction System
- Define `CompletionTransaction` interface in `packages/core/src/tx.ts`
- Implement creation function with secp256k1 signing
- Create validation functions for MCQ/FRQ formats

### Phase 2: Batch Processing
- Implement batch validator with integrity checks
- Add batch signature verification
- Create batch optimization utilities

### Phase 3: Testing & Validation
- Comprehensive Vitest test suite in `packages/core/tests/tx.test.ts`
- Test transaction creation, validation, and batching
- Edge case testing for malformed data

### Phase 4: PoK Integration
- Integrate with attestation system from ADR-012
- Enable consensus-based verification
- Support for distributed validation

## Benefits

1. **Granular Progress Tracking**: Per-question completion visibility
2. **Social Consensus Ready**: Designed for emergent verification model
3. **Question Type Flexibility**: Supports both MCQ and FRQ formats
4. **Network Efficiency**: Batching reduces P2P overhead
5. **Cryptographic Integrity**: Signatures ensure data authenticity
6. **Offline Capability**: Local storage prep enables offline functionality

## Consequences

**Positive:**
- Enables detailed learning analytics and progress tracking
- Supports peer-to-peer verification without centralized answer keys
- Provides foundation for gamification and achievement systems
- Maintains student privacy through hash-based MCQ answers

**Negative:**
- Increases transaction volume compared to lesson-level tracking
- Requires additional validation logic for different question types
- Batching adds complexity to transaction processing
- May increase local storage requirements

## References

- [ADR-012: Social Consensus and Proof of Knowledge](./012-social-consensus-and-proof-of-knowledge.md)
- [ADR-025: Unified Granular JSON Schema for Curriculum and Questions](./025-unified-granular-json-schema-for-curriculum-and-questions.md)
- [secp256k1 Signature Standards](https://github.com/bitcoin-core/secp256k1)

## Success Criteria

- [ ] CompletionTransaction interface supports both MCQ and FRQ formats
- [ ] Transaction creation with valid secp256k1 signatures
- [ ] Batch validator processes 5-10 transactions efficiently
- [ ] 100% test coverage for transaction creation and validation
- [ ] Integration ready for social consensus attestation system 