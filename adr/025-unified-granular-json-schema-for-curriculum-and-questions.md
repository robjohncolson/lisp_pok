# ADR-025: Unified Granular JSON Schema for Curriculum and Questions

**Date:** 2025-01-25  
**Status:** Accepted  
**Context:** V2 Development Phase - Blockchain-Powered Student Experience  

## Context

Building on the foundational work of [ADR-021: Canonical V2 Curriculum Data Structure](./021-canonical-v2-curriculum-data-structure.md) and [ADR-024: AP Statistics Quiz Rendering and Conversion System](./024-ap-statistics-quiz-rendering-and-conversion-system.md), we face a critical architectural decision regarding data consolidation and schema validation for our curriculum system.

Currently, our educational content exists in three separate data structures:
1. **`curriculumData.ts`** - Core curriculum structure with lessons, videos, and activities
2. **`lessons_export.json`** - Simplified lesson metadata with activity contributions
3. **`questions_export.json`** - Question metadata with asset references

This fragmentation creates several challenges:
- **Data Synchronization Issues**: Multiple sources of truth for overlapping information
- **Schema Validation Gaps**: No runtime validation of complex nested structures
- **Offline-First Limitations**: Inconsistent data format hinders local caching strategies
- **PoK Integration Barriers**: Proof-of-Knowledge system requires standardized question formats
- **Distribution Tracking Absence**: No mechanism for tracking student answer patterns

## Decision

We adopt a **unified granular JSON schema** that consolidates all curriculum and question data into a single, strongly-typed, Zod-validated structure within `packages/data`. This schema will support:

### Core Schema Features

1. **Per-Question Granularity**: Each question is a self-contained unit with complete metadata
2. **Question Type Support**: 
   - **MCQs**: ID, prompt, options array with keys/values, correct answer hash
   - **FRQs**: ID, prompt, structured rubric with scoring parts, solution text
3. **Hashed Asset Verification**: SHA-256 hashes for all images and media assets
4. **Emergent Distribution Fields**: Answer choice tracking for analytics and PoK consensus

### Schema Structure

```typescript
// Core curriculum structure
interface CurriculumSchema {
  units: CurriculumUnit[];
  metadata: {
    version: string;
    generatedAt: string;
    totalQuestions: number;
    questionHashMap: Record<string, string>;
  };
}

// Question types with granular detail
interface MCQQuestion {
  id: string;
  type: 'multiple-choice';
  prompt: string;
  options: Array<{
    key: string;
    value: string;
  }>;
  answerKey: string;
  answerHash: string;
  reasoning?: string;
  assetHash?: string;
  distributionTracker: {
    A: number[];
    B: number[];
    C: number[];
    D: number[];
    E: number[];
  };
}

interface FRQQuestion {
  id: string;
  type: 'free-response';
  prompt: string;
  solution: {
    parts: Array<{
      partId: string;
      description: string;
      response: string;
      calculations?: string[];
    }>;
    scoring: {
      totalPoints: number;
      rubric: Array<{
        part: string;
        maxPoints: number;
        criteria: string[];
        scoringNotes?: string;
      }>;
    };
  };
  assetHash?: string;
  distributionTracker: {
    scores: number[];
    attempts: number[];
  };
}
```

### Integration Points

**Offline-First Architecture**: Single JSON artifact enables complete offline functionality with embedded questions, assets, and metadata.

**Proof-of-Knowledge Integration**: Standardized question hashing and distribution tracking support consensus mechanisms for student progress verification.

**Asset Verification**: SHA-256 hashes ensure content integrity across distributed systems and enable efficient caching strategies.

## Implementation Strategy

### Phase 1: Schema Definition
- Create Zod schema in `packages/data/src/curriculumSchema.ts`
- Define TypeScript interfaces derived from Zod schemas
- Implement validation functions and sample data generators

### Phase 2: Data Migration
- Update `curriculumData.ts` to use new schema structure
- Migrate existing JSON files into unified format
- Embed 89 lessons with ~1000 questions following ADR-021 structure

### Phase 3: Validation & Testing
- Comprehensive Vitest test suite for schema validation
- Edge case testing for malformed data
- Performance benchmarks for large datasets

### Phase 4: Integration
- Update quiz renderer to consume new schema
- Implement distribution tracking mechanisms
- Enable PoK integration points

## Benefits

1. **Single Source of Truth**: Eliminates data synchronization issues
2. **Runtime Validation**: Zod provides compile-time and runtime type safety
3. **Offline Optimization**: Complete curriculum data in single exportable artifact
4. **Distribution Analytics**: Built-in tracking for student response patterns
5. **Content Integrity**: Cryptographic hashing ensures data verification
6. **PoK Readiness**: Standardized format enables blockchain integration

## Risks and Mitigations

**Risk**: Large JSON file size impacts performance
**Mitigation**: Implement lazy loading and compression strategies

**Risk**: Migration complexity from existing data structures
**Mitigation**: Gradual migration with backward compatibility layers

**Risk**: Schema evolution challenges
**Mitigation**: Versioned schema with migration utilities

## References

- [ADR-021: Canonical V2 Curriculum Data Structure](./021-canonical-v2-curriculum-data-structure.md)
- [ADR-024: AP Statistics Quiz Rendering and Conversion System](./024-ap-statistics-quiz-rendering-and-conversion-system.md)
- [Zod Documentation](https://zod.dev/)
- [Vitest Testing Framework](https://vitest.dev/)

## Success Criteria

- [ ] Schema validates all existing curriculum data without errors
- [ ] Test suite achieves 100% coverage of schema validation paths
- [ ] Performance benchmarks show acceptable load times for complete dataset
- [ ] Quiz renderer successfully consumes new schema format
- [ ] Distribution tracking functions operate correctly with empty initial states 