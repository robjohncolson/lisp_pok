# test_app.py
import pytest
import time
import math
from app import app, POKEngine, Node, Transaction, Payload, Block

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def engine():
    return POKEngine('pok_curriculum_trimmed.json')

@pytest.fixture
def sample_node(engine):
    node = engine.add_node('test_pubkey', 'aces')
    return node

# A. API Endpoint & Basic State Tests

def test_init(client):
    response = client.get('/init')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'initialized'
    assert 'curriculum_length' in data

def test_add_node(client):
    response = client.post('/node/add', json={'pubkey': 'test_pubkey', 'archetype': 'aces'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'node added'
    assert data['pubkey'] == 'test_pubkey'

# B. Core Logic Unit Tests (Testing the POKEngine Class Directly)

def test_calculate_convergence_mcq(engine, sample_node):
    # Add nodes for attesters
    engine.add_node('pub1', 'diligent')
    engine.add_node('pub2', 'diligent')
    engine.add_node('pub3', 'strugglers')
    # Predefined MCQ attestations: two 'A', one 'B' -> convergence 2/3
    txn1 = engine.create_txn('q1', 'pub1', 'A', time.time() - 10, 'attestation')
    txn2 = engine.create_txn('q1', 'pub2', 'A', time.time() - 5, 'attestation')
    txn3 = engine.create_txn('q1', 'pub3', 'B', time.time(), 'attestation')
    sample_node.mempool = [txn1, txn2, txn3]
    conv = engine.calculate_convergence(sample_node, 'q1')
    assert math.isclose(conv, 2/3, rel_tol=1e-9)

def test_propose_block_quorum(engine, sample_node):
    # Dynamic quorum: assume early progress (min 2 attestations)
    engine.add_node('pub1', 'diligent')
    engine.add_node('pub2', 'diligent')
    sample_node.progress = 0  # First half
    completion = engine.create_txn('q1', 'test_pubkey', 'A', time.time(), 'completion')
    attns = [engine.create_txn('q1', f'pub{i}', 'A', time.time(), 'attestation') for i in range(1, 3)]
    sample_node.mempool = [completion] + attns
    engine.propose_pok_block(sample_node)
    assert len(sample_node.chain) == 1
    assert sample_node.chain[0].type == 'pok'
    assert len(sample_node.mempool) == 0  # Cleared

def test_propose_block_insufficient_quorum(engine, sample_node):
    # Insufficient: only 1 attestation for min 2
    engine.add_node('pub1', 'diligent')
    sample_node.progress = 0
    completion = engine.create_txn('q1', 'test_pubkey', 'A', time.time(), 'completion')
    attns = [engine.create_txn('q1', 'pub1', 'A', time.time(), 'attestation')]
    sample_node.mempool = [completion] + attns
    engine.propose_pok_block(sample_node)
    assert len(sample_node.chain) == 0  # No block
    assert len(sample_node.mempool) == 2  # Unchanged

# C. Advanced Logic & Architectural Validation Tests

def test_logarithmic_scaling_convergence(engine, sample_node):
    # Setup two attesters: low rep (10), high rep (1000), both vote 'A'
    engine.add_node('low_rep', 'diligent')
    engine.nodes['low_rep'].reputation = 10
    engine.add_node('high_rep', 'aces')
    engine.nodes['high_rep'].reputation = 1000
    txn_low = engine.create_txn('q1', 'low_rep', 'A', time.time(), 'attestation')
    txn_high = engine.create_txn('q1', 'high_rep', 'A', time.time(), 'attestation')
    sample_node.mempool = [txn_low, txn_high]
    conv = engine.calculate_convergence(sample_node, 'q1', weighted=True)
    weight_low = math.log1p(10)
    weight_high = math.log1p(1000)
    expected_conv = (weight_low + weight_high) / (weight_low + weight_high)
    assert math.isclose(conv, expected_conv, rel_tol=1e-9)
    assert not math.isclose(weight_high / weight_low, 100, rel_tol=0.1)  # Not linear
    assert math.isclose(weight_high / weight_low, math.log1p(1000) / math.log1p(10), rel_tol=1e-9)  # Log scaled

def test_thought_leader_bonus(engine, sample_node):
    # Setup: mined txn 'A', early and late attestations
    engine.add_node('pub0', 'aces')
    engine.add_node('early', 'aces')
    engine.nodes['early'].reputation = 1.0
    engine.add_node('late', 'diligent')
    engine.nodes['late'].reputation = 1.0
    # Create attestations with timestamps to simulate early (<50%) and late (>50%)
    attn_early = engine.create_txn('q1', 'early', 'A', time.time() - 20, 'attestation')
    attn_late = engine.create_txn('q1', 'late', 'A', time.time() - 10, 'attestation')
    sample_node.mempool = [attn_early, attn_late]
    # Update history to reflect proportions at time of attestations
    sample_node.consensus_history['q1'] = [
        {attn_early.timestamp: {'A': 0.4}},  # Early: below threshold
        {attn_late.timestamp: {'A': 0.6}}    # Late: above threshold
    ]
    mined_txn = engine.create_txn('q1', 'pub0', 'A', time.time(), 'completion')
    engine._update_reputation(sample_node, [mined_txn])
    expected_early_rep = 1.0 + engine.thought_leader_bonus * math.log1p(1.0)
    expected_late_rep = 1.0 + 1.0 * math.log1p(1.0)
    assert math.isclose(engine.nodes['early'].reputation, expected_early_rep, rel_tol=1e-9)
    assert math.isclose(engine.nodes['late'].reputation, expected_late_rep, rel_tol=1e-9)

def test_teacher_reveal_weight(engine, sample_node):
    # Setup: one standard attn 'A', one ap_reveal 'A' (weight 10)
    engine.add_node('pub1', 'diligent')
    engine.add_node('teacher', 'teacher')
    txn_standard = engine.create_txn('q1', 'pub1', 'A', time.time(), 'attestation')
    txn_reveal = engine.create_txn('q1', 'teacher', 'A', time.time(), 'ap_reveal')
    sample_node.mempool = [txn_standard, txn_reveal]
    conv = engine.calculate_convergence(sample_node, 'q1', weighted=True)
    weight_standard = math.log1p(1.0)  # Default rep 1.0
    weight_reveal = 10.0
    expected_conv = (weight_standard + weight_reveal) / (weight_standard + weight_reveal)
    assert math.isclose(conv, expected_conv, rel_tol=1e-9)
    assert weight_reveal > weight_standard * 5  # Significantly higher

def test_onboarding_provisional_reputation(engine):
    # Setup existing nodes with reps: [5, 10, 15] -> median 10
    engine.add_node('pub1', 'diligent')
    engine.nodes['pub1'].reputation = 5
    engine.add_node('pub2', 'diligent')
    engine.nodes['pub2'].reputation = 10
    engine.add_node('pub3', 'diligent')
    engine.nodes['pub3'].reputation = 15
    new_node = engine.add_node('new_pub', 'diligent')
    assert math.isclose(new_node.reputation, 10, rel_tol=1e-9)