#!/usr/bin/env python3
"""
Fix node types in witchcraft_data.js

The bug: All nodes were classified as "unknown" instead of properly being
classified as "accused" or "witness" based on:
1. Node ID containing "witch" or "Witch" -> accused
2. Source of TESTIFIED_AGAINST edge -> witness
"""

import re
import json

INPUT_FILE = "/Users/sarahbonanno/Desktop/Witchcraft/witchcraft_data.js"
OUTPUT_FILE = "/Users/sarahbonanno/Desktop/Witchcraft/witchcraft_data.js"

def extract_data_from_js(js_content):
    """Extract the DATA object from the JS file."""
    # Find the JSON-like content after "const DATA = "
    match = re.search(r'const DATA = (\{.*\});?\s*$', js_content, re.DOTALL)
    if not match:
        raise ValueError("Could not find DATA object in JS file")

    json_str = match.group(1)

    # Convert JS object notation to valid JSON
    # Only quote top-level property names (which appear after newline+spaces)
    # These are: waves, coefficients, network, survival, temporal, scatter
    json_str = re.sub(r'\n(\s+)(waves|coefficients|network|survival|temporal|scatter):', r'\n\1"\2":', json_str)

    return json.loads(json_str)

def extract_trial_id(accused_name):
    """Extract trial ID from accused name like 'B 2192 no 2, witch 003, ...'"""
    # Look for patterns like "witch 003" or "Witch 123"
    match = re.search(r'\bwitch\s*(\d+)', accused_name, re.IGNORECASE)
    if match:
        return f"w{match.group(1).zfill(3)}"
    # Also try "B XXXX" pattern
    match = re.search(r'^B\s*(\d+)', accused_name)
    if match:
        return f"B{match.group(1)}"
    return None


def fix_node_types(data):
    """Fix node types based on ID patterns and edge relationships."""

    nodes = data['network']['nodes']
    links = data['network']['links']

    # Build sets for each role (a person can have multiple roles)
    is_accused = set()
    is_witness = set()
    is_family = set()

    # Track edge participation and trial connections
    node_edges = {}
    node_trials = {}  # Track which trials each person is connected to

    for node in nodes:
        node_edges[node['id']] = {'as_source': [], 'as_target': []}
        node_trials[node['id']] = set()

    for link in links:
        src, tgt = link['source'], link['target']
        rel_type = link.get('type', 'UNKNOWN')
        if src in node_edges:
            node_edges[src]['as_source'].append((rel_type, tgt))
        if tgt in node_edges:
            node_edges[tgt]['as_target'].append((rel_type, src))

    # Step 1: Identify accused by "witch" in node ID (case insensitive)
    for node in nodes:
        node_id = node['id']
        if re.search(r'\bwitch\b', node_id, re.IGNORECASE):
            is_accused.add(node_id)
            trial_id = extract_trial_id(node_id)
            if trial_id:
                node_trials[node_id].add(trial_id)

    # Step 2: Identify from TESTIFIED_AGAINST edges and link trials
    for link in links:
        if link.get('type') == 'TESTIFIED_AGAINST':
            accused = link['target']
            witness = link['source']
            is_accused.add(accused)
            is_witness.add(witness)

            # Link witness to the trial of the accused
            trial_id = extract_trial_id(accused)
            if trial_id:
                node_trials[witness].add(trial_id)
                node_trials[accused].add(trial_id)

    # Step 3: Identify co-witnesses and link trials
    for link in links:
        if link.get('type') == 'CO_WITNESS':
            src, tgt = link['source'], link['target']
            is_witness.add(src)
            is_witness.add(tgt)
            # Share trial info between co-witnesses
            shared_trials = node_trials[src] | node_trials[tgt]
            node_trials[src].update(shared_trials)
            node_trials[tgt].update(shared_trials)

    # Step 4: Identify family members and link trials
    kinship_types = {'SPOUSE_OF', 'WIDOW_OF', 'CHILD_OF', 'SIBLING_OF'}
    for link in links:
        if link.get('type') in kinship_types:
            src, tgt = link['source'], link['target']
            is_family.add(src)
            is_family.add(tgt)
            # Share trial info with family members
            shared_trials = node_trials[src] | node_trials[tgt]
            node_trials[src].update(shared_trials)
            node_trials[tgt].update(shared_trials)

    # Step 5: Determine composite types (allow overlaps)
    counts = {'accused': 0, 'witness': 0, 'family': 0, 'family_witness': 0, 'unknown': 0}

    for node in nodes:
        node_id = node['id']

        roles = []
        if node_id in is_accused:
            roles.append('accused')
        if node_id in is_witness:
            roles.append('witness')
        if node_id in is_family and node_id not in is_accused:
            roles.append('family')

        # Determine type based on roles
        if 'accused' in roles:
            node['type'] = 'accused'
            counts['accused'] += 1
        elif 'witness' in roles and 'family' in roles:
            node['type'] = 'family_witness'
            counts['family_witness'] += 1
        elif 'witness' in roles:
            node['type'] = 'witness'
            counts['witness'] += 1
        elif 'family' in roles:
            node['type'] = 'family'
            counts['family'] += 1
        else:
            node['type'] = 'unknown'
            counts['unknown'] += 1

        # Add trial info to node
        trials = sorted(node_trials[node_id])
        if trials:
            node['trials'] = trials

    print(f"Node type classification:")
    print(f"  Accused:        {counts['accused']}")
    print(f"  Witness:        {counts['witness']}")
    print(f"  Family:         {counts['family']}")
    print(f"  Family+Witness: {counts['family_witness']}")
    print(f"  Unknown:        {counts['unknown']}")
    print(f"  Total:          {len(nodes)}")

    return data

def write_js_file(data, output_path):
    """Write the fixed data back to a JS file."""
    js_content = "const DATA = " + json.dumps(data, indent=None, ensure_ascii=False) + ";\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

def main():
    print("Loading witchcraft_data.js...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        js_content = f.read()

    print("Parsing data...")
    data = extract_data_from_js(js_content)

    print("Fixing node types...")
    fixed_data = fix_node_types(data)

    print(f"Writing fixed data to {OUTPUT_FILE}...")
    write_js_file(fixed_data, OUTPUT_FILE)

    print("Done!")

if __name__ == "__main__":
    main()
