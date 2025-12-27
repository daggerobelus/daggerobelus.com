#!/usr/bin/env python3
"""
Extract Social Network from Witch Trial JSONs

Parses all trial JSON files and extracts a complete social network
graph with all persons as nodes and all relationships as edges.

Output: D3-ready JSON file for visualization
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Paths
TRIALS_DIR = Path(__file__).parent.parent / "extracted" / "trials"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "network_complete.json"


def normalize_name(name):
    """Normalize a name for comparison/deduplication."""
    if not name:
        return None
    # Lowercase, strip whitespace, normalize spaces
    name = re.sub(r'\s+', ' ', name.lower().strip())
    # Remove common prefixes/suffixes that vary
    name = re.sub(r'^(la |le |l\')', '', name)
    return name


def create_node_id(name, trial_id, node_type, index=0):
    """Create a unique node ID."""
    safe_name = re.sub(r'[^a-z0-9]', '_', normalize_name(name) or 'unknown')[:30]
    return f"{trial_id}_{node_type}_{safe_name}_{index}"


def extract_year(date_str):
    """Extract year from various date formats."""
    if not date_str:
        return None
    # Try to find a 4-digit year
    match = re.search(r'\b(1[4-7]\d{2})\b', str(date_str))
    if match:
        return int(match.group(1))
    return None


def extract_nodes_and_edges(trial_data, trial_id):
    """Extract all nodes and edges from a single trial."""
    nodes = []
    edges = []

    # Track node IDs for this trial to create edges
    accused_nodes = {}
    witness_nodes = {}

    trial_year = extract_year(trial_data.get('trial_date_start'))
    trial_location = trial_data.get('location', {})
    location_str = trial_location.get('town') if isinstance(trial_location, dict) else str(trial_location)

    # === ACCUSED NODES ===
    for i, accused in enumerate(trial_data.get('accused', [])):
        if not accused.get('name'):
            continue

        node_id = create_node_id(accused['name'], trial_id, 'accused', i)
        accused_nodes[i] = node_id

        nodes.append({
            'id': node_id,
            'name': accused.get('name'),
            'type': 'accused',
            'trial_id': trial_id,
            'gender': accused.get('gender'),
            'age': accused.get('age'),
            'occupation': accused.get('occupation'),
            'residence': accused.get('residence'),
            'economic_status': accused.get('economic_status'),
            'practiced_healing': accused.get('practiced_healing'),
            'healing_types': accused.get('healing_types', []),
            'outcome': trial_data.get('outcome'),
            'year': trial_year,
            'location': location_str
        })

    # === WITNESS NODES ===
    for i, witness in enumerate(trial_data.get('witnesses', [])):
        if not witness.get('name'):
            continue

        node_id = create_node_id(witness['name'], trial_id, 'witness', i)
        witness_nodes[i] = node_id

        nodes.append({
            'id': node_id,
            'name': witness.get('name'),
            'type': 'witness',
            'trial_id': trial_id,
            'gender': witness.get('gender'),
            'age': witness.get('age'),
            'occupation': witness.get('occupation'),
            'residence': witness.get('residence'),
            'relationship_to_accused': witness.get('relationship_to_accused'),
            'credibility_assessment': witness.get('credibility_assessment'),
            'year': trial_year,
            'location': location_str
        })

        # Create testified_against edges to all accused
        for acc_idx, acc_node_id in accused_nodes.items():
            edges.append({
                'source': node_id,
                'target': acc_node_id,
                'type': 'testified_against',
                'trial_id': trial_id,
                'year': trial_year,
                'weight': 1
            })

    # === FORMAL ACCUSER NODE ===
    formal_accuser = trial_data.get('formal_accuser', {})
    if formal_accuser and formal_accuser.get('name'):
        fa_node_id = create_node_id(formal_accuser['name'], trial_id, 'accuser', 0)

        nodes.append({
            'id': fa_node_id,
            'name': formal_accuser.get('name'),
            'type': 'formal_accuser',
            'trial_id': trial_id,
            'occupation': formal_accuser.get('occupation'),
            'residence': formal_accuser.get('location'),
            'relationship_to_accused': formal_accuser.get('relationship_to_accused'),
            'year': trial_year,
            'location': location_str
        })

        # Create formally_accused edges
        for acc_idx, acc_node_id in accused_nodes.items():
            edges.append({
                'source': fa_node_id,
                'target': acc_node_id,
                'type': 'formally_accused',
                'trial_id': trial_id,
                'year': trial_year,
                'weight': 2  # Higher weight for formal accusation
            })

    # === VICTIM NODES (from harms_catalog) ===
    victim_nodes = {}
    for i, harm in enumerate(trial_data.get('harms_catalog', [])):
        victim_name = harm.get('victim_name')
        if not victim_name or victim_name.lower() in ['unknown', 'unnamed', 'various']:
            continue

        # Avoid duplicate victims in same trial
        norm_name = normalize_name(victim_name)
        if norm_name in victim_nodes:
            victim_node_id = victim_nodes[norm_name]
        else:
            victim_node_id = create_node_id(victim_name, trial_id, 'victim', len(victim_nodes))
            victim_nodes[norm_name] = victim_node_id

            nodes.append({
                'id': victim_node_id,
                'name': victim_name,
                'type': 'victim',
                'trial_id': trial_id,
                'year': trial_year,
                'location': location_str
            })

        # Create allegedly_harmed edges from accused to victim
        for acc_idx, acc_node_id in accused_nodes.items():
            edges.append({
                'source': acc_node_id,
                'target': victim_node_id,
                'type': 'allegedly_harmed',
                'harm_type': harm.get('harm_type'),
                'result': harm.get('result'),
                'trial_id': trial_id,
                'year': trial_year,
                'weight': 1
            })

    # === THIRD PARTY NODES ===
    for i, third_party in enumerate(trial_data.get('third_parties', [])):
        if not third_party.get('name'):
            continue

        tp_node_id = create_node_id(third_party['name'], trial_id, 'third_party', i)

        nodes.append({
            'id': tp_node_id,
            'name': third_party.get('name'),
            'type': 'third_party',
            'trial_id': trial_id,
            'role': third_party.get('role'),
            'residence': third_party.get('location'),
            'year': trial_year,
            'location': location_str
        })

    # === ACCOMPLICE NODES (named in confessions) ===
    confession = trial_data.get('confession_details', {})
    accomplices = confession.get('accomplices_named', []) if confession else []

    for i, accomplice in enumerate(accomplices):
        acc_name = accomplice.get('name') if isinstance(accomplice, dict) else accomplice
        if not acc_name:
            continue

        accomplice_node_id = create_node_id(acc_name, trial_id, 'accomplice', i)

        nodes.append({
            'id': accomplice_node_id,
            'name': acc_name,
            'type': 'named_accomplice',
            'trial_id': trial_id,
            'year': trial_year,
            'location': location_str
        })

        # Create named_as_accomplice edges from accused
        for acc_idx, acc_node_id in accused_nodes.items():
            edges.append({
                'source': acc_node_id,
                'target': accomplice_node_id,
                'type': 'named_as_accomplice',
                'trial_id': trial_id,
                'year': trial_year,
                'weight': 2  # High weight - sabbat accusation
            })

    # === RELATIONSHIP EDGES ===
    for rel in trial_data.get('relationships', []):
        person1 = rel.get('person1')
        person2 = rel.get('person2')
        rel_type = rel.get('relationship_type', 'associated_with')

        if not person1 or not person2:
            continue

        # Try to find existing nodes, or create new ones
        p1_id = create_node_id(person1, trial_id, 'person', 0)
        p2_id = create_node_id(person2, trial_id, 'person', 1)

        edges.append({
            'source': p1_id,
            'target': p2_id,
            'type': rel_type,
            'description': rel.get('description'),
            'trial_id': trial_id,
            'year': trial_year,
            'weight': 1
        })

    return nodes, edges


def build_network():
    """Build complete network from all trial JSONs."""
    all_nodes = []
    all_edges = []
    trials_processed = 0
    errors = []

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Process all trial files
    json_files = sorted(TRIALS_DIR.glob("w*.json"))

    print(f"Found {len(json_files)} trial JSON files")

    for json_file in json_files:
        trial_id = json_file.stem

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                trial_data = json.load(f)

            nodes, edges = extract_nodes_and_edges(trial_data, trial_id)
            all_nodes.extend(nodes)
            all_edges.extend(edges)
            trials_processed += 1

        except Exception as e:
            errors.append(f"{trial_id}: {str(e)}")
            print(f"Error processing {trial_id}: {e}")

    # Calculate statistics
    node_types = defaultdict(int)
    for node in all_nodes:
        node_types[node['type']] += 1

    edge_types = defaultdict(int)
    for edge in all_edges:
        edge_types[edge['type']] += 1

    # Build output structure
    network = {
        'nodes': all_nodes,
        'edges': all_edges,
        'metadata': {
            'generated': datetime.now().isoformat(),
            'trials_processed': trials_processed,
            'total_nodes': len(all_nodes),
            'total_edges': len(all_edges),
            'node_types': dict(node_types),
            'edge_types': dict(edge_types),
            'errors': errors
        }
    }

    # Write output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(network, f, indent=2, ensure_ascii=False)

    print(f"\n=== Network Extraction Complete ===")
    print(f"Trials processed: {trials_processed}")
    print(f"Total nodes: {len(all_nodes)}")
    print(f"Total edges: {len(all_edges)}")
    print(f"\nNode types:")
    for ntype, count in sorted(node_types.items(), key=lambda x: -x[1]):
        print(f"  {ntype}: {count}")
    print(f"\nEdge types:")
    for etype, count in sorted(edge_types.items(), key=lambda x: -x[1]):
        print(f"  {etype}: {count}")
    print(f"\nOutput written to: {OUTPUT_FILE}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for err in errors[:10]:
            print(f"  {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    return network


if __name__ == '__main__':
    build_network()
