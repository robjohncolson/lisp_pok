from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from pok_engine import POKEngine

app = Flask(__name__)
CORS(app)
# Attach the engine directly to the Flask app object
app.engine = POKEngine('pok_curriculum_trimmed.json') 


@app.route('/txn/create', methods=['POST'])
def create_txn():
    data = request.json
    txn = app.engine.create_txn(data['qid'], data['pubkey'], data['ans'], time.time(), data['type'])
    # Add to node's mempool (assume pubkey exists)
    node = app.engine.nodes.get(data['pubkey'])
    if node:
        node.mempool.append(txn)
        return jsonify({"status": "success", "txn_id": txn.id}), 201
    return jsonify({"error": "Node not found"}), 404

@app.route('/sync', methods=['POST'])
def sync_nodes():
    data = request.json
    node1 = app.engine.nodes.get(data['pubkey1'])
    node2 = app.engine.nodes.get(data['pubkey2'])
    if node1 and node2:
        app.engine.sync_nodes(node1, node2)
        return jsonify({"status": "sync complete"}), 200
    return jsonify({"error": "Nodes not found"}), 404

@app.route('/block/propose/<pubkey>', methods=['POST'])
def propose_block(pubkey: str):
    node = app.engine.nodes.get(pubkey)
    if node:
        app.engine.propose_attestation_block(node)
        app.engine.propose_pok_block(node)
        return jsonify({"chain_length": len(node.chain)}), 200
    return jsonify({"error": "Node not found"}), 404

@app.route('/node/add', methods=['POST'])
def add_node():
    data = request.json
    node = app.engine.add_node(data['pubkey'], data['archetype'], data.get('provisional_reputation'))
    return jsonify({"status": "node added", "pubkey": node.pubkey}), 201

@app.route('/convergence/<pubkey>/<qid>', methods=['GET'])
def get_convergence(pubkey: str, qid: str):
    node = app.engine.nodes.get(pubkey)
    if node:
        conv = app.engine.calculate_convergence(node, qid, weighted=True)
        return jsonify({"convergence": conv}), 200
    return jsonify({"error": "Node not found"}), 404

@app.route('/ap_reveal', methods=['POST'])
def ap_reveal():
    data = request.json
    app.engine.submit_ap_reveal(data['teacher_pubkey'], data['qid'], data['ans'])
    return jsonify({"status": "ap_reveal submitted"}), 201

if __name__ == '__main__':
    app.run(debug=True)