# verify_sim.py (v1.1 - Final Verified Version)

import time
import random
import statistics
from collections import Counter

# CRITICAL: Import the verified classes directly from our canonical app.py
from app import POKEngine, Node, Question, Transaction

# --- Simulation Parameters (Canonized) ---
SIM_DAYS = 30
MEETINGS_PER_WEEK = 4
QUESTIONS_PER_DAY = 5
TOTAL_NODES = 40
CLASS_SIZE = 20

ARCHETYPES = {
    'aces': 0.95,
    'diligent': 0.80,
    'strugglers': 0.60,
    'guessers': 0.25
}

# --- Metric Calculation Functions ---

def calculate_truth_accuracy(engine: POKEngine) -> float:
    correct_mcqs = 0
    total_mined_mcqs = 0
    
    all_mined_completions = [txn for node in engine.nodes.values() for block in node.chain if block.type == 'pok' for txn in block.txns if txn.type == 'completion']

    for txn in all_mined_completions:
        question = next((q for q in engine.curriculum if q.id == txn.question_id), None)
        if question and question.qtype == 'mcq' and question.answer_key:
            total_mined_mcqs += 1
            if txn.payload.answer == question.answer_key:
                correct_mcqs += 1
                
    return (correct_mcqs / total_mined_mcqs) * 100 if total_mined_mcqs > 0 else 100.0

def calculate_block_latency(engine: POKEngine) -> float:
    latencies = []
    # Find all completion transactions that have been mined
    all_mined_completions = [
        txn for node in engine.nodes.values()
        for block in node.chain if block.type == 'pok'
        for txn in block.txns if txn.type == 'completion'
    ]

    if not all_mined_completions:
        return 0.0

    for txn in all_mined_completions:
        # Check if the transaction has our simulation metadata
        if hasattr(txn, 'creation_day') and hasattr(txn, 'mined_day'):
            latency = txn.mined_day - txn.creation_day
            if latency >= 0:
                latencies.append(latency)

    return statistics.mean(latencies) if latencies else 0.0

def calculate_chain_fragmentation(engine: POKEngine) -> float:
    if not engine.nodes: return 0.0
    chain_lengths = [len(n.chain) for n in engine.nodes.values()]
    if not chain_lengths: return 0.0
    
    try:
        max_len = max(chain_lengths)
    except ValueError:
        return 0.0

    if max_len == 0: return 0.0
    
    fragmented_nodes = sum(1 for length in chain_lengths if length < max_len)
    return (fragmented_nodes / TOTAL_NODES) * 100

# --- Main Simulation Logic ---

def run_simulation():
    print("--- Starting APStat Chain E2E Verification Simulation ---")
    
    engine = POKEngine('pok_curriculum_trimmed.json')
    if not engine.curriculum:
        print("FATAL: Could not load curriculum. Make sure 'pok_curriculum_trimmed.json' exists.")
        return

    # 1. Setup Nodes
    classes = {'a': [], 'b': []}
    archetype_distribution = (['aces'] * 4 + ['diligent'] * 24 + ['strugglers'] * 8 + ['guessers'] * 4)
    random.shuffle(archetype_distribution)
    
    for i in range(TOTAL_NODES):
        class_key = 'a' if i < CLASS_SIZE else 'b'
        pubkey = f'pub_{class_key}_{i % CLASS_SIZE}'
        engine.add_node(pubkey, archetype_distribution[i])
        classes[class_key].append(pubkey)

    print(f"Initialized {TOTAL_NODES} nodes across 2 classrooms.")

    # --- Simulation Loop ---
    daily_fragmentation_log = []

    for day in range(1, SIM_DAYS + 1):
        print(f"\n--- Day {day}/{SIM_DAYS} ---")
        
        # PHASE 1: SOLO WORK
        for node in engine.nodes.values():
            for _ in range(QUESTIONS_PER_DAY):
                q_index = node.progress % len(engine.curriculum)
                q = engine.curriculum[q_index]
                
                is_correct = random.random() < ARCHETYPES.get(node.archetype, 0.5)
                ans = q.answer_key if is_correct and q.answer_key else 'B'
                
                txn = engine.create_txn(q.id, node.pubkey, ans, time.time(), 'completion')
                setattr(txn, 'creation_day', day) # Attach simulation metadata
                node.mempool.append(txn)
                node.progress += 1
        
        print(f"Solo work complete. Avg progress: {statistics.mean([n.progress for n in engine.nodes.values()]):.1f} questions.")

        # PHASE 2: MEETING & SYNC
        if (day - 1) % 5 < MEETINGS_PER_WEEK:
            print("Meeting Day: Running sync, attestation, and mining...")
            
            all_pubkeys = list(engine.nodes.keys())
            random.shuffle(all_pubkeys)
            
            for i in range(0, len(all_pubkeys) - 1, 2):
                node1 = engine.nodes[all_pubkeys[i]]
                node2 = engine.nodes[all_pubkeys[i+1]]
                engine.sync_nodes(node1, node2)

                for node, partner in [(node1, node2), (node2, node1)]:
                    partner_completions = [t for t in partner.mempool if t.type == 'completion']
                    if partner_completions:
                        num_to_attest = random.randint(1, min(3, len(partner_completions)))
                        txns_to_attest = random.sample(partner_completions, num_to_attest)
                        
                        for txn_to_attest in txns_to_attest:
                            q = next((q for q in engine.curriculum if q.id == txn_to_attest.question_id), None)
                            if q:
                                is_correct = random.random() < ARCHETYPES.get(node.archetype, 0.5)
                                ans = q.answer_key if is_correct and q.answer_key else 'B'
                                attestation_txn = engine.create_txn(q.id, node.pubkey, ans, time.time(), 'attestation')
                                node.mempool.append(attestation_txn)

            for node in engine.nodes.values():
                chain_len_before = len(node.chain)
                engine.propose_attestation_block(node)
                engine.propose_pok_block(node)
                
                if len(node.chain) > chain_len_before:
                    for block_index in range(chain_len_before, len(node.chain)):
                        new_block = node.chain[block_index]
                        if new_block.type == 'pok':
                            for txn in new_block.txns:
                                if txn.type == 'completion' and not hasattr(txn, 'mined_day'):
                                    setattr(txn, 'mined_day', day)

        # PHASE 3: END OF DAY LOGGING
        daily_fragmentation_log.append(calculate_chain_fragmentation(engine))
        print(f"End of Day {day}. Fragmentation: {daily_fragmentation_log[-1]:.1f}%")

    # --- Final Report Generation ---
    print("\n--- Simulation Complete. Generating Final Report... ---")
    
    final_accuracy = calculate_truth_accuracy(engine)
    final_latency = calculate_block_latency(engine)
    final_fragmentation = statistics.mean(daily_fragmentation_log) if daily_fragmentation_log else 0.0

    with open('simulation_results_python.md', 'w') as f:
        f.write("# Python E2E Simulation Results\n\n")
        f.write("This report was generated by the canonical `verify_sim.py` using the verified `app.py` engine.\n\n")
        f.write(f"- **Truth Accuracy:** {final_accuracy:.1f}%\n")
        f.write(f"- **Block Latency:** {final_latency:.1f} days\n")
        f.write(f"- **Average Chain Fragmentation:** {final_fragmentation:.1f}%\n")

    print("Report 'simulation_results_python.md' generated successfully.")
    print(f"Final Metrics:\n  Accuracy: {final_accuracy:.1f}%\n  Latency: {final_latency:.1f} days\n  Fragmentation: {final_fragmentation:.1f}%")


if __name__ == '__main__':
    run_simulation()