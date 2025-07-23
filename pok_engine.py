import json
import hashlib
import time
import random
import math
from typing import List, Dict
from schemas import Payload, Transaction, Block, Question, Node

class POKEngine:
    """
    Core engine for APStat Chain, implementing emergent consensus, reputation, and sync logic.
    Translated from final_simulation.rkt.
    """
    def __init__(self, curriculum_file: str):
        self.curriculum = self.load_curriculum(curriculum_file)
        self.nodes: Dict[str, Node] = {}  # pubkey -> Node
        self.quorum_conv_thresh = 0.7
        self.thought_leader_thresh = 0.5
        self.thought_leader_bonus = 2.5
        self.cleanup_age = 3  # days for incentivized cleanup

    def load_curriculum(self, file: str) -> List[Question]:
        """Loads curriculum from JSON file."""
        with open(file, 'r') as f:
            data = json.load(f)
            return [Question(q['id'], q['prompt'], q['type'], q.get('choices', []), q.get('answerKey')) for q in data]

    def create_txn(self, qid: str, pubkey: str, ans: str, t: float, txn_type: str) -> Transaction:
        """Creates a new transaction."""
        txn_hash = hashlib.sha256(ans.encode()).hexdigest()
        return Transaction(f"{t}-{txn_type}", t, pubkey, qid, txn_type, Payload(ans, txn_hash))

    def calculate_convergence(self, node: Node, qid: str, weighted: bool = False) -> float:
        """Calculates convergence score for a question, optionally with reputation weighting."""
        all_txns = node.mempool + [txn for block in node.chain for txn in block.txns]
        attns = [txn for txn in all_txns if txn.question_id == qid and txn.type in ("attestation", "ap_reveal")]
        dist: Dict[str, float] = {}
        for txn in attns:
            weight = 10 if txn.type == "ap_reveal" else (math.log(self.nodes[txn.owner_pubkey].reputation + 1) if weighted else 1)
            dist[txn.payload.hash] = dist.get(txn.payload.hash, 0) + weight
        total = sum(dist.values())
        return max(dist.values()) / total if total > 0 else 0.0

    def propose_attestation_block(self, node: Node):
        """Proposes a lightweight attestation block if quorum met."""
        attns = [txn for txn in node.mempool if txn.type == "attestation"]
        if len(attns) >= 5:
            block_hash = f"{len(node.chain)}-att-block"
            new_block = Block(block_hash, attns, "attestation")
            node.chain.append(new_block)
            node.mempool = [txn for txn in node.mempool if txn not in attns]

    def propose_pok_block(self, node: Node):
        """Proposes a PoK block with dynamic quorum."""
        mempool = node.mempool
        q_index = node.progress
        min_attest = 2 if q_index < len(self.curriculum) // 2 else 4
        valid_txns = []
        for txn in mempool:
            if txn.type == "completion":
                conv = self.calculate_convergence(node, txn.question_id, weighted=True)  # Log scaling
                attns_count = len([t for t in (mempool + [tx for b in node.chain for tx in b.txns]) if t.question_id == txn.question_id and t.type in ("attestation", "ap_reveal")])
                if attns_count >= min_attest and conv >= self.quorum_conv_thresh:
                    valid_txns.append(txn)
        if valid_txns:
            block_hash = f"{len(node.chain)}-pok-block"
            new_block = Block(block_hash, valid_txns, "pok")
            node.chain.append(new_block)
            node.mempool = [txn for txn in node.mempool if txn not in valid_txns]
            self.update_reputation(node, valid_txns)

    def update_reputation(self, node: Node, mined_txns: List[Transaction]):
        """Updates reputation with Thought Leader bonus and log scaling."""
        for txn in mined_txns:
            qid = txn.question_id
            final_ans_hash = txn.payload.hash
            attns = [t for t in (node.mempool + [tx for b in node.chain for tx in b.txns]) if t.question_id == qid and t.type in ("attestation", "ap_reveal")]
            for attn in attns:
                attester_pubkey = attn.owner_pubkey
                attester = self.nodes.get(attester_pubkey)
                if attester and attn.payload.hash == final_ans_hash:
                    hist = node.consensus_history.get(qid, [])
                    prop_at_time = self._lookup_prop(hist, attn.timestamp)
                    bonus = self.thought_leader_bonus if prop_at_time < self.thought_leader_thresh else 1.0
                    weight = math.log(attester.reputation + 1)
                    attester.reputation += bonus * weight

    def _lookup_prop(self, hist: List[Dict[float, Dict[str, float]]], timestamp: float) -> float:
        """Looks up proportion at timestamp (simplified interpolation)."""
        if not hist:
            return 0.0
        # Sort hist by timestamp and find closest
        sorted_hist = sorted(hist, key=lambda x: list(x.keys())[0])
        for entry in sorted_hist:
            ts = list(entry.keys())[0]
            if ts >= timestamp:
                return max(entry[ts].values()) if entry[ts] else 0.0
        return max(sorted_hist[-1][list(sorted_hist[-1].keys())[0]].values())  # Last state

    def sync_nodes(self, node1: Node, node2: Node):
        """Syncs two nodes with longest chain rule and 25% gossip for attestations."""
        if len(node1.chain) < len(node2.chain):
            node1.chain = node2.chain[:]
        elif len(node2.chain) < len(node1.chain):
            node2.chain = node1.chain[:]
        combined_attns = [txn for txn in (node1.mempool + node2.mempool + [tx for b in (node1.chain + node2.chain) for tx in b.txns]) if txn.type == "attestation"]
        gossip_attns = random.sample(combined_attns, int(len(combined_attns) * 0.25)) if combined_attns else []
        node1.mempool.extend([txn for txn in (node2.mempool + gossip_attns) if txn not in node1.mempool])
        node2.mempool.extend([txn for txn in (node1.mempool + gossip_attns) if txn not in node2.mempool])
        # Update history post-sync (simplified)
        for qid in set([txn.question_id for txn in gossip_attns]):
            self._update_consensus_history(node1, qid)
            self._update_consensus_history(node2, qid)

    def _update_consensus_history(self, node: Node, qid: str):
        """Updates consensus history snapshot."""
        current_time = time.time()
        dist = {}
        all_txns = node.mempool + [txn for block in node.chain for txn in block.txns]
        attns = [txn for txn in all_txns if txn.question_id == qid and txn.type == "attestation" and txn.timestamp <= current_time]
        for txn in attns:
            dist[txn.payload.hash] = dist.get(txn.payload.hash, 0) + 1
        total = sum(dist.values())
        proportions = {k: v / total if total > 0 else 0 for k, v in dist.items()}
        if qid not in node.consensus_history:
            node.consensus_history[qid] = []
        node.consensus_history[qid].append({current_time: proportions})

    def add_node(self, pubkey: str, archetype: str, provisional_reputation: Optional[float] = None) -> Node:
        """Adds a new node, with provisional reputation if onboarding."""
        node = Node(pubkey, archetype, [], [], 0, provisional_reputation or 0.0, {})
        self.nodes[pubkey] = node
        return node

    def submit_ap_reveal(self, teacher_pubkey: str, qid: str, ans: str):
        """Submits a weighted AP reveal from teacher."""
        txn = self.create_txn(qid, teacher_pubkey, ans, time.time(), "ap_reveal")
        # Broadcast to all nodes (simplified: add to a random node mempool)
        random_node = random.choice(list(self.nodes.values()))
        random_node.mempool.append(txn)