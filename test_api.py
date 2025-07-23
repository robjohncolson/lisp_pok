# test_api.py
import pytest
import time
from app import app
from pok_engine import POKEngine, Block

# REPLACE the old client fixture with this one
@pytest.fixture
def client():
    # Reset the engine's state before each test
    app.engine = POKEngine('pok_curriculum_trimmed.json')
    
    # Create all nodes that will participate in the tests
    app.engine.add_node('pub0', 'aces')
    app.engine.add_node('pub1', 'aces')
    app.engine.add_node('pub2', 'diligent')
    app.engine.add_node('pub3', 'diligent')
    app.engine.add_node('pub4', 'strugglers')
    
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_create_txn(client):
    response = client.post('/txn/create', json={'qid': 'q1', 'pubkey': 'pub1', 'ans': 'A', 'type': 'completion'})
    assert response.status_code == 201
    assert len(app.engine.nodes['pub1'].mempool) == 1

def test_sync_nodes(client):
    # Setup chains
    app.engine.nodes['pub1'].chain = [Block('b1', [], 'pok'), Block('b2', [], 'pok')]
    app.engine.nodes['pub2'].chain = [Block('b1', [], 'pok')]
    response = client.post('/sync', json={'pubkey1': 'pub1', 'pubkey2': 'pub2'})
    assert response.status_code == 200
    assert len(app.engine.nodes['pub2'].chain) == 2  # Longest chain wins

def test_propose_block(client):
    app.engine.nodes['pub1'].mempool = [app.engine.create_txn('q1', 'pub1', 'A', time.time(), 'completion')]
    # Add enough attns for quorum
    for i in range(5):
        app.engine.nodes['pub1'].mempool.append(app.engine.create_txn('q1', f'pub{i}', 'A', time.time(), 'attestation'))
    response = client.post('/block/propose/pub1')
    assert response.status_code == 200
    assert len(app.engine.nodes['pub1'].chain) > 0
    assert len(app.engine.nodes['pub1'].mempool) == 0