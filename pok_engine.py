# pok_engine.py

import json
import hashlib
import time
import random
import math
from typing import List, Dict, Optional
from schemas import Payload, Transaction, Block, Question, Node

class POKEngine:
    """
    Core engine for APStat Chain, implementing emergent consensus, reputation, and sync logic.
    Faithfully translated from the validated final_simulation.rkt.
    """
    def __init__(self, curriculum_file: str):
        self.curriculum = self._load_curriculum(curriculum_file)
        self.nodes: Dict[str, Node] = {}  # pubkey -> Node
        self.quorum_conv_thresh = 0.7
        self.thought_leader_thresh = 0.5
        self.thought_leader_bonus = 2.5
        self.cleanup_age = 3  # days
    
    # ADD THIS METHOD INSIDE THE POKEngine CLASS
def sync_nodes(self, node1: Node, node2: Node):
    """Syncs two nodes with longest chain rule and 25% gossip for attestations."""
    # Longest chain wins
    if len(node1.chain) < len(node2.chain):
        node1.chain = list(node2.chain) # Use list() to create a copy
    elif len(node2.chain) < len(node1.chain):
        node2.chain = list(node1.chain) # Use list() to create a copy

    # Combine mempools to find all unique attestations
    all_attestations = {
        t.id: t for t in (node1.mempool + node2.mempool) if t.type == "attestation"
    }
    
    # Gossip: each node learns about a sample of all unique attestations
    gossip_sample_size = int(len(all_attestations) * 0.25)
    gossip_ids = random.sample(list(all_attestations.keys()), gossip_sample_size)
    gossip_txns = [all_attestations[id] for id in gossip_ids]

    # Merge mempools: add txns from partner that you don't have
    node1_mempool_ids = {t.id for t in node1.mempool}
    node2_mempool_ids = {t.id for t in node2.mempool}

    node1.mempool.extend([t for t in node2.mempool if t.id not in node1_mempool_ids])
    node2.mempool.extend([t for t in node1.mempool if t.id not in node2_mempool_ids])
    
    # Add gossiped attestations
    node1.mempool.extend([t for t in gossip_txns if t.id not in node1_mempool_ids])
    node2.mempool.extend([t for t in gossip_txns if t.id not in node2_mempool_ids])

    def _load_curriculum(self, file_path: str) -> List[Question]:
        """Loads curriculum from a JSON file. Private method."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Handle potential key variations from JS curriculum file
                return [
                    Question(
                        id=q.get('id'),
                        prompt=q.get('prompt'),
                        qtype=q.get('type', 'mcq'), # default to mcq if not specified
                        choices=q.get('attachments', {}).get('choices', []),
                        answer_key=q.get('attachments', {}).get('answerKey')
                    ) for q in data
                ]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading curriculum: {e}")
            return []

    def add_node(self, pubkey: str, archetype: str, provisional_reputation: Optional[float] = 0.0) -> Node:
        """Adds a new node to the engine's registry."""
        if pubkey in self.nodes:
            # Return existing node if it's already there
            return self.nodes[pubkey]
        node = Node(
            pubkey=pubkey,
            archetype=archetype,
            mempool=[],
            chain=[],
            progress=0,
            reputation=provisional_reputation or 1.0, # Start with 1.0 reputation to avoid log(0)
            consensus_history={}
        )
        self.nodes[pubkey] = node
        return node

    def create_txn(self, qid: str, pubkey: str, ans: str, t: float, txn_type: str) -> Transaction:
        """Creates a new transaction object."""
        txn_hash = hashlib.sha256(str(ans).encode()).hexdigest()
        payload = Payload(answer=str(ans), hash=txn_hash)
        return Transaction(
            id=f"{t}-{pubkey[:5]}-{txn_type}",
            timestamp=t,
            owner_pubkey=pubkey,
            question_id=qid,
            type=txn_type,
            payload=payload
        )

    def calculate_convergence(self, node: Node, qid: str, weighted: bool = False) -> float:
        """Calculates convergence score for a question, optionally with reputation weighting."""
        all_txns = node.mempool + [txn for block in node.chain for txn in block.txns]
        attns = [txn for txn in all_txns if txn.question_id == qid and txn.type in ("attestation", "ap_reveal")]
        dist: Dict[str, float] = {}
        
        for txn in attns:
            attester_pubkey = txn.owner_pubkey
            if attester_pubkey not in self.nodes: continue # Ignore attestations from unknown nodes
                
            weight = 1.0
            if txn.type == "ap_reveal":
                weight = 10.0
            elif weighted:
                # Use math.log1p for log(x+1) to handle reputation=0 gracefully
                weight = math.log1p(self.nodes[attester_pubkey].reputation)
            
            dist[txn.payload.hash] = dist.get(txn.payload.hash, 0) + weight

        total_weight = sum(dist.values())
        return max(dist.values()) / total_weight if total_weight > 0 else 0.0

    def propose_attestation_block(self, node: Node):
        """Proposes a lightweight attestation block."""
        attns = [txn for txn in node.mempool if txn.type == "attestation"]
        if len(attns) >= 5:
            block_hash = f"{len(node.chain)}-att-block"
            new_block = Block(block_hash, attns, "attestation")
            node.chain.append(new_block)
            mined_ids = {t.id for t in attns}
            node.mempool = [txn for txn in node.mempool if txn.id not in mined_ids]

    def propose_pok_block(self, node: Node):
        """Proposes a PoK block with dynamic quorum."""
        minable_completions = []
        for txn in node.mempool:
            if txn.type == "completion" and txn.owner_pubkey == node.pubkey:
                min_attest = 2 if node.progress < len(self.curriculum) / 2 else 4
                
                all_visible_txns = node.mempool + [tx for b in node.chain for tx in b.txns]
                attns_for_this_txn = [t for t in all_visible_txns if t.question_id == txn.question_id and t.type == "attestation"]
                
                attns_count = len(attns_for_this_txn)
                conv = self.calculate_convergence(node, txn.question_id, weighted=True)
                
                if attns_count >= min_attest and conv >= self.quorum_conv_thresh:
                    minable_completions.append(txn)

        if not minable_completions:
            return

        minable_qids = {t.question_id for t in minable_completions}
        related_attestations = [t for t in node.mempool if t.question_id in minable_qids and t.type == "attestation"]
        
        txns_for_block = minable_completions + related_attestations
        
        block_hash = f"{len(node.chain)}-pok-block"
        new_block = Block(block_hash, txns_for_block, "pok")
        node.chain.append(new_block)
        
        mined_txn_ids = {t.id for t in txns_for_block}
        node.mempool = [t for t in node.mempool if t.id not in mined_txn_ids]
        
        self._update_reputation(node, minable_completions)

    def _update_reputation(self, node: Node, mined_txns: List[Transaction]):
        """Updates reputation with Thought Leader bonus. Private method."""
        for txn in mined_txns:
            qid = txn.question_id
            final_ans_hash = txn.payload.hash
            
            all_visible_txns = node.mempool + [tx for b in node.chain for tx in b.txns]
            attns = [t for t in all_visible_txns if t.question_id == qid and t.type == "attestation"]
            
            for attn in attns:
                attester_pubkey = attn.owner_pubkey
                attester = self.nodes.get(attester_pubkey)

                if attester and attn.payload.hash == final_ans_hash:
                    # Simplified logic for now, as history tracking isn't fully built
                    is_early = (time.time() - attn.timestamp) > 15 
                    bonus = self.thought_leader_bonus if is_early else 1.0
                    weight = math.log1p(attester.reputation)
                    attester.reputation += bonus * weight