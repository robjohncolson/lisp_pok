from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Payload:
    """Represents the payload of a transaction."""
    answer: str
    hash: str

@dataclass
class Transaction:
    """Represents a blockchain transaction."""
    id: str
    timestamp: float
    owner_pubkey: str
    question_id: str
    type: str  # "completion", "attestation", "ap_reveal"
    payload: Payload

@dataclass
class Block:
    """Represents a blockchain block."""
    hash: str
    txns: List[Transaction]
    type: str  # "attestation" or "pok"

@dataclass
class Question:
    """Represents a curriculum question."""
    id: str
    prompt: str
    qtype: str  # "mcq" or "frq"
    choices: List[Dict[str, str]]
    answer_key: Optional[str]

@dataclass
class Node:
    """Represents a network node (student or teacher)."""
    pubkey: str
    archetype: str
    mempool: List[Transaction]
    chain: List[Block]
    progress: int
    reputation: float
    consensus_history: Dict[str, List[Dict[float, Dict[str, float]]]]  # timestamp -> {ans_hash: proportion}