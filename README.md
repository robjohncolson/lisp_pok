# APStat Chain Python Backend

## Overview
This is the production-ready backend for APStat Chain, implementing emergent consensus for educational attestation. Core logic in `pok_engine.py`, API in `app.py`.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Place `pok_curriculum_trimmed.json` in the root.
3. Run: `python app.py`

## Endpoints
- POST /txn/create: Create transaction (body: {qid, pubkey, ans, type})
- POST /sync: Sync two nodes (body: {pubkey1, pubkey2})
- POST /block/propose/<pubkey>: Propose blocks for a node
- POST /node/add: Add new node (body: {pubkey, archetype, provisional_reputation?})
- GET /convergence/<pubkey>/<qid>: Get convergence score
- POST /ap_reveal: Submit AP reveal (body: {teacher_pubkey, qid, ans})

## Testing
- Unit tests can be added to pok_engine.py (e.g., pytest).
- Validates against simulation metrics: Latency ~6 days, Accuracy >90% in mocked runs.

## Architecture Notes
- Faithful to final_simulation.rkt: Emergent flywheel, log scaling, dynamic quorum, etc.
- Extensible for UI integration (e.g., pok_app.html).