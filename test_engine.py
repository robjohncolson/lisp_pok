# test_engine.py
import pytest
import time
from pok_engine import POKEngine
from schemas import Node, Transaction, Payload, Block

@pytest.fixture
def engine():
    return POKEngine('pok_curriculum_trimmed.json')

@pytest.fixture
def sample_node(engine):
    node = Node('test_pubkey', 'aces', [], [], 0, 1.0, {})
    engine.nodes['test_pubkey'] = node
    return node

def test_calculate_convergence(engine, sample_node):
    engine.add_node('pub1', 'aces')
    engine.add_node('pub2', 'diligent')
    engine.add_node('pub3', 'strugglers')
    # Predefined attestations
    txn1 = engine.create_txn('q1', 'pub1', 'A', time.time() - 10, 'attestation')
    txn2 = engine.create_txn('q1', 'pub2', 'A', time.time() - 5, 'attestation')
    txn3 = engine.create_txn('q1', 'pub3', 'B', time.time(), 'attestation')
    sample_node.mempool = [txn1, txn2, txn3]
    conv = engine.calculate_convergence(sample_node, 'q1')
    assert conv == 2/3  # Two 'A' out of three

def test_update_reputation(engine, sample_node):
    # Mock mined txn and attns
    mined_txn = engine.create_txn('q1', 'pub0', 'A', time.time(), 'completion')
    attn1 = engine.create_txn('q1', 'pub1', 'A', time.time() - 20, 'attestation')  # Early
    attn2 = engine.create_txn('q1', 'pub2', 'A', time.time() - 10, 'attestation')  # Late
    sample_node.mempool = [attn1, attn2]
    sample_node.consensus_history['q1'] = [{time.time() - 20: {'A': 0.4}}, {time.time() - 10: {'A': 0.6}}]
    engine.nodes['pub1'] = Node('pub1', 'aces', [], [], 0, 1.0, {})
    engine.nodes['pub2'] = Node('pub2', 'diligent', [], [], 0, 1.0, {})
    engine.update_reputation(sample_node, [mined_txn])
    assert engine.nodes['pub1'].reputation > 1.0 + engine.thought_leader_bonus  # Bonus applied
    assert engine.nodes['pub2'].reputation > 1.0  # Standard bonus

def test_propose_pok_block(engine, sample_node):
    engine.add_node('pub1', 'aces') # The attester needs to exist

    # Dynamic quorum: early progress (min 2)
    sample_node.progress = 0  # First half
    completion = engine.create_txn('q1', 'test_pubkey', 'A', time.time(), 'completion')
    attns = [engine.create_txn('q1', 'pub1', 'A', time.time(), 'attestation') for _ in range(2)]
    sample_node.mempool = [completion] + attns
    engine.propose_pok_block(sample_node)
    assert len(sample_node.chain) == 1  # Block proposed
    assert len(sample_node.mempool) == 0  # Cleared