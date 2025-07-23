# app.py (v1.0 - Canonized)
import json
import hashlib
import time
import random
import math
import statistics  # Needed for median calculation
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from flask import Flask, request, jsonify


# --- DATASTRUCTURES / SCHEMAS ---
@dataclass
class Payload:
    answer: str
    hash: str


@dataclass
class Transaction:
    id: str
    timestamp: float
    owner_pubkey: str
    question_id: str
    type: str
    payload: Payload


@dataclass
class Block:
    hash: str
    txns: List[Transaction]
    type: str


@dataclass
class Question:
    id: str
    prompt: str
    qtype: str
    choices: List[Dict[str, str]]
    answer_key: Optional[str]


@dataclass
class Node:
    pubkey: str
    archetype: str
    mempool: List[Transaction] = field(default_factory=list)
    chain: List[Block] = field(default_factory=list)
    progress: int = 0
    reputation: float = 1.0  # Start with 1.0 to avoid log(0) issues
    consensus_history: Dict = field(default_factory=dict)


# --- CORE ENGINE CLASS ---
class POKEngine:
    def __init__(self, curriculum_file: str):
        self.curriculum = self._load_curriculum(curriculum_file)
        self.nodes: Dict[str, Node] = {}
        self.quorum_conv_thresh = 0.7
        self.thought_leader_thresh = 0.5
        self.thought_leader_bonus = 2.5

    def _load_curriculum(self, file_path: str) -> List[Question]:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return [
                    Question(
                        id=q.get("id"),
                        prompt=q.get("prompt"),
                        qtype=q.get("type", "mcq"),
                        choices=q.get("attachments", {}).get("choices", []),
                        answer_key=q.get("attachments", {}).get("answerKey"),
                    )
                    for q in data
                ]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def add_node(
        self,
        pubkey: str,
        archetype: str,
        provisional_reputation: Optional[float] = None,
    ) -> Node:
        if pubkey in self.nodes:
            return self.nodes[pubkey]

        if provisional_reputation is None:
            if self.nodes:
                reps = [node.reputation for node in self.nodes.values()]
                provisional_reputation = statistics.median(reps) if reps else 1.0
            else:
                provisional_reputation = 1.0

        node = Node(
            pubkey=pubkey, archetype=archetype, reputation=provisional_reputation
        )
        self.nodes[pubkey] = node
        return node

    def create_txn(
        self, qid: str, pubkey: str, ans: str, t: float, txn_type: str
    ) -> Transaction:
        txn_hash = hashlib.sha256(str(ans).encode()).hexdigest()
        return Transaction(
            id=f"{t}-{pubkey[:5]}-{txn_type}",
            timestamp=t,
            owner_pubkey=pubkey,
            question_id=qid,
            type=txn_type,
            payload=Payload(answer=str(ans), hash=txn_hash),
        )

    def calculate_convergence(
        self, node: Node, qid: str, weighted: bool = False
    ) -> float:
        all_txns = node.mempool + [txn for block in node.chain for txn in block.txns]
        attns = [
            txn
            for txn in all_txns
            if txn.question_id == qid and txn.type in ("attestation", "ap_reveal")
        ]
        dist: Dict[str, float] = {}

        for txn in attns:
            attester_pubkey = txn.owner_pubkey
            if attester_pubkey not in self.nodes:
                continue

            weight = 1.0
            if txn.type == "ap_reveal":
                weight = 10.0
            elif weighted:
                weight = math.log1p(self.nodes[attester_pubkey].reputation)

            dist[txn.payload.hash] = dist.get(txn.payload.hash, 0) + weight

        total_weight = sum(dist.values())
        return max(dist.values()) / total_weight if total_weight > 0 else 0.0

    def propose_attestation_block(self, node: Node):
        attns = [txn for txn in node.mempool if txn.type == "attestation"]
        if len(attns) >= 5:
            block_hash = f"{len(node.chain)}-att-block"
            new_block = Block(block_hash, attns, "attestation")
            node.chain.append(new_block)
            mined_ids = {t.id for t in attns}
            node.mempool = [txn for txn in node.mempool if txn.id not in mined_ids]

    def propose_pok_block(self, node: Node):
        minable_completions = []
        for txn in node.mempool:
            if txn.type == "completion" and txn.owner_pubkey == node.pubkey:
                min_attest = 2 if node.progress < len(self.curriculum) / 2 else 4
                all_visible_txns = node.mempool + [
                    tx for b in node.chain for tx in b.txns
                ]
                attns_for_txn = [
                    t
                    for t in all_visible_txns
                    if t.question_id == txn.question_id and t.type == "attestation"
                ]

                if (
                    len(attns_for_txn) >= min_attest
                    and self.calculate_convergence(node, txn.question_id)
                    >= self.quorum_conv_thresh
                ):
                    minable_completions.append(txn)

        if not minable_completions:
            return

        minable_qids = {t.question_id for t in minable_completions}
        related_attestations = [
            t
            for t in node.mempool
            if t.question_id in minable_qids and t.type == "attestation"
        ]

        txns_for_block = minable_completions + related_attestations

        block_hash = f"{len(node.chain)}-pok-block"
        new_block = Block(block_hash, txns_for_block, "pok")
        node.chain.append(new_block)

        mined_txn_ids = {t.id for t in txns_for_block}
        node.mempool = [t for t in node.mempool if t.id not in mined_txn_ids]
        self._update_reputation(node, minable_completions)

    def _update_reputation(self, node: Node, mined_txns: List[Transaction]):
        """Updates reputation with Thought Leader bonus and logarithmic scaling."""
        for txn in mined_txns:
            qid = txn.question_id
            final_ans_hash = txn.payload.hash
            all_visible_txns = node.mempool + [tx for b in node.chain for tx in b.txns]
            attns = [
                t
                for t in all_visible_txns
                if t.question_id == qid and t.type == "attestation"
            ]

            # Sort attestations by timestamp
            attns.sort(key=lambda x: x.timestamp)

            # Initialize running distribution
            dist = {}
            total_count = 0

            for attn in attns:
                attester = self.nodes.get(attn.owner_pubkey)
                if attester and attn.payload.hash == final_ans_hash:
                    # Calculate proportion at time of attestation
                    prop_at_time = (
                        max(dist.values()) / total_count
                        if total_count > 0 and dist
                        else 0.0
                    )
                    bonus = (
                        self.thought_leader_bonus
                        if prop_at_time < self.thought_leader_thresh
                        else 1.0
                    )
                    weight = math.log1p(attester.reputation)
                    attester.reputation += bonus * weight

                    # Update running distribution
                    dist[attn.payload.hash] = dist.get(attn.payload.hash, 0) + 1
                    total_count += 1

    def _lookup_prop(self, hist: List, timestamp: float) -> float:
        """Helper method to lookup proportion at a given timestamp."""
        # Implementation needed - placeholder for now
        return 0.0


# --- APPLICATION INITIALIZATION ---
app = Flask(__name__)
engine = POKEngine("pok_curriculum_trimmed.json")


# --- API ROUTES ---
@app.route("/init", methods=["GET"])
def init():
    return jsonify(
        {"status": "initialized", "curriculum_length": len(engine.curriculum)}
    )


@app.route("/node/add", methods=["POST"])
def add_node_route():
    data = request.json
    if not data or "pubkey" not in data or "archetype" not in data:
        return jsonify({"error": "Missing pubkey or archetype"}), 400

    node = engine.add_node(data["pubkey"], data["archetype"])
    return jsonify({"status": "node added", "pubkey": node.pubkey}), 201


# ... Add other routes here when needed ...

if __name__ == "__main__":
    app.run(debug=True)
