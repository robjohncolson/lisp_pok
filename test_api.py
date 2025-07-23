# test_api.py
import pytest
import time
from app import app
from schemas import Block

@pytest.fixture
def client():
    # Reset the engine's state before each test
    app.engine.nodes = {} # Clear nodes
    app.engine.add_node('pub0', 'aces')
    app.engine.add_node('pub1', 'aces')
    app.engine.add_node('pub2', 'diligent')
    app.engine.add_node('pub3', 'strugglers')
    app.engine.add_node('pub4', 'guessers')
    
    # Clear mempool/chain for the primary test node
    app.engine.nodes['pub1'].mempool = []
    app.engine.nodes['pub1'].chain = []

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
    app.engine.nodes['pub2'].chain = [Block('b1', [], 'pok')] # Shorter chain
    
    # Before sync, node2 has a shorter chain
    assert len(app.engine.nodes['pub2'].chain) == 1
    
    response = client.post('/sync', json={'pubkey1': 'pub1', 'pubkey2': 'pub2'})
    assert response.status_code == 200
    
    # After sync, node2 should adopt the longer chain from node1
    assert len(app.engine.nodes['pub2'].chain) == 2

def test_propose_block(client):
    # Node 'pub1' has its own completion transaction
    app.engine.nodes['pub1'].mempool.append(
        app.engine.create_txn('q1', 'pub1', 'A', time.time(), 'completion')
    )
    # 'pub1' has received attestations from other nodes
    for i in range(5):
        attester_pubkey = f'pub{i}'
        app.engine.nodes['pub1'].mempool.append(
            app.engine.create_txn('q1', attester_pubkey, 'A', time.time(), 'attestation')
        )
    
    # Propose a block
    response = client.post('/block/propose/pub1')
    assert response.status_code == 200
    
    assert len(app.engine.nodes['pub1'].chain) == 1
    assert len(app.engine.nodes['pub1'].mempool) == 0