#!/usr/bin/env python3
"""
Extract Healer Network from Witch Trial JSONs

Focuses specifically on trials where the accused practiced healing.
Builds a network showing:
- Healers (accused with practiced_healing: true)
- Their healing relationships (who they healed)
- Their accusation relationships (who accused them of harm)
- "Paradox cases" where the same person was both healed and harmed

Output: D3-ready JSON file for visualization clustered by healing type
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Paths
TRIALS_DIR = Path(__file__).parent.parent / "extracted" / "trials"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "healer_network.json"


def normalize_name(name):
    """Normalize a name for comparison/deduplication."""
    if not name:
        return None
    name = re.sub(r'\s+', ' ', name.lower().strip())
    name = re.sub(r'^(la |le |l\')', '', name)
    return name


def extract_year(dates_obj):
    """Extract year from dates object."""
    if not dates_obj:
        return None
    start = dates_obj.get('start', '')
    if start:
        match = re.search(r'(\d{4})', str(start))
        if match:
            return int(match.group(1))
    return None


def find_healing_evidence(trial_data):
    """
    Find evidence of healing acts in the trial record.
    Returns list of healing relationships.
    """
    healing_acts = []

    # Check harms_catalog for healing mentions
    for harm in trial_data.get('harms_catalog', []):
        method = harm.get('method_alleged', '') or ''
        if any(word in method.lower() for word in ['soup', 'cure', 'heal', 'remedy']):
            healing_acts.append({
                'target': harm.get('victim_name'),
                'type': 'soup_healing',
                'context': method,
                'later_accused': True  # They appear in harms catalog
            })

    # Check material_culture for healing items
    for item in trial_data.get('material_culture', []):
        if item.get('category') == 'food' and 'soup' in item.get('context', '').lower():
            healing_acts.append({
                'target': 'community',
                'type': 'soup_healing',
                'context': item.get('context'),
                'later_accused': False
            })

    # Check notable_quotes for healing mentions
    for quote in trial_data.get('notable_quotes', []):
        context = quote.get('context', '').lower()
        if any(word in context for word in ['heal', 'cure', 'soup', 'remedy']):
            healing_acts.append({
                'target': 'unknown',
                'type': 'healing_mention',
                'context': quote.get('english', quote.get('french', '')),
                'later_accused': False
            })

    return healing_acts


def extract_healer_data(trial_data, trial_id):
    """Extract healer-specific data from a trial."""
    healers = []

    trial_year = extract_year(trial_data.get('dates'))
    trial_location = trial_data.get('location', '')
    outcome = trial_data.get('outcome', '')

    for i, accused in enumerate(trial_data.get('accused', [])):
        if not accused.get('practiced_healing'):
            continue

        healer_id = f"{trial_id}_healer_{i}"

        # Get healing types
        healing_types = accused.get('healing_types', [])
        if not healing_types:
            healing_types = ['unspecified']

        # Determine primary healing type for clustering
        type_priority = ['midwifery', 'herbal_remedies', 'veterinary',
                        'touch_healing', 'charms_amulets', 'other', 'unspecified']
        primary_type = 'unspecified'
        for t in type_priority:
            if t in healing_types:
                primary_type = t
                break

        # Build victims list (people allegedly harmed)
        victims = []
        for harm in trial_data.get('harms_catalog', []):
            victim_name = harm.get('victim_name')
            if victim_name and victim_name.lower() not in ['unknown', 'unnamed']:
                victims.append({
                    'name': victim_name,
                    'harm_type': harm.get('harm_category', 'unknown'),
                    'harm_description': harm.get('harm_description', ''),
                    'quarrel': harm.get('precipitating_quarrel', ''),
                    'method': harm.get('method_alleged', ''),
                    'witness_number': harm.get('witness_number')
                })

        # Build witnesses list
        witnesses = []
        for w in trial_data.get('witnesses', []):
            testimony = w.get('testimony', {})
            witnesses.append({
                'name': w.get('name'),
                'age': w.get('age'),
                'gender': w.get('gender'),
                'relationship': w.get('relationship_to_accused'),
                'reputation_years': testimony.get('reputation_duration_years'),
                'quarrel': testimony.get('quarrel_subject'),
                'threat_received': testimony.get('threat_received', False),
                'threat_quote': testimony.get('threat_quote'),
                'harms_alleged': testimony.get('harms_alleged', [])
            })

        # Find healing evidence
        healing_acts = find_healing_evidence(trial_data)

        # Check for paradox cases (healed then accused by same person)
        paradox_cases = []
        for act in healing_acts:
            target_norm = normalize_name(act.get('target', ''))
            for victim in victims:
                victim_norm = normalize_name(victim.get('name', ''))
                if target_norm and victim_norm and target_norm == victim_norm:
                    paradox_cases.append({
                        'person': victim.get('name'),
                        'healing_context': act.get('context'),
                        'harm_type': victim.get('harm_type'),
                        'harm_description': victim.get('harm_description')
                    })

        # Get confession details if available
        confession = accused.get('confession', {})

        healer = {
            'id': healer_id,
            'trial_id': trial_id,
            'name': accused.get('name', 'Unknown'),
            'gender': accused.get('gender'),
            'age': accused.get('age'),
            'age_approximate': accused.get('age_approximate', False),
            'occupation': accused.get('occupation', []),
            'economic_status': accused.get('economic_status'),
            'residence': accused.get('residence'),
            'origin': accused.get('origin'),
            'marital_status': accused.get('marital_status'),

            # Healing specific
            'healing_types': healing_types,
            'primary_healing_type': primary_type,
            'healing_acts': healing_acts,

            # Trial context
            'trial_year': trial_year,
            'trial_location': trial_location,
            'outcome': outcome,
            'torture_used': trial_data.get('torture', {}).get('used', False),

            # Network data
            'victims': victims,
            'witnesses': witnesses,
            'witness_count': len(trial_data.get('witnesses', [])),

            # Paradox analysis
            'paradox_cases': paradox_cases,
            'has_paradox': len(paradox_cases) > 0,

            # Confession details
            'confessed': confession.get('confessed', False),
            'confessed_under_torture': confession.get('under_torture', False),
            'retracted': confession.get('retracted', False),
            'sabbat_attended': confession.get('sabbat_attended', False),

            # Key quotes
            'notable_quotes': trial_data.get('notable_quotes', [])
        }

        healers.append(healer)

    return healers


def build_network_edges(healers):
    """Build edges for the network visualization."""
    edges = []

    for healer in healers:
        healer_id = healer['id']

        # Testimony edges (witness -> healer)
        for i, witness in enumerate(healer['witnesses']):
            if witness['name']:
                witness_id = f"{healer['trial_id']}_witness_{i}"

                # Determine edge strength based on testimony
                weight = 1
                if witness.get('harms_alleged'):
                    weight = 2
                if witness.get('threat_received'):
                    weight += 1
                if witness.get('reputation_years') and witness['reputation_years'] > 10:
                    weight += 1

                edges.append({
                    'source': witness_id,
                    'target': healer_id,
                    'type': 'testified_against',
                    'weight': weight,
                    'trial_id': healer['trial_id'],
                    'quarrel': witness.get('quarrel'),
                    'relationship': witness.get('relationship')
                })

        # Harm edges (healer -> victim)
        for i, victim in enumerate(healer['victims']):
            if victim['name']:
                victim_id = f"{healer['trial_id']}_victim_{normalize_name(victim['name'])}"

                # Check if this is a paradox case
                is_paradox = any(
                    normalize_name(p['person']) == normalize_name(victim['name'])
                    for p in healer['paradox_cases']
                )

                edges.append({
                    'source': healer_id,
                    'target': victim_id,
                    'type': 'allegedly_harmed',
                    'harm_type': victim['harm_type'],
                    'method': victim['method'],
                    'is_paradox': is_paradox,
                    'trial_id': healer['trial_id'],
                    'quarrel': victim['quarrel']
                })

                # If paradox, add a healing edge too
                if is_paradox:
                    edges.append({
                        'source': healer_id,
                        'target': victim_id,
                        'type': 'healed',
                        'is_paradox': True,
                        'trial_id': healer['trial_id']
                    })

    return edges


def build_cluster_data(healers):
    """Organize healers into clusters by healing type."""
    clusters = defaultdict(list)

    for healer in healers:
        primary_type = healer['primary_healing_type']
        clusters[primary_type].append(healer['id'])

    # Define cluster display properties
    cluster_info = {
        'midwifery': {
            'name': 'Midwives',
            'description': 'Women who assisted with childbirth',
            'color': '#e74c3c',
            'icon': 'baby'
        },
        'herbal_remedies': {
            'name': 'Herbalists',
            'description': 'Healers using plants and natural remedies',
            'color': '#27ae60',
            'icon': 'leaf'
        },
        'veterinary': {
            'name': 'Animal Healers',
            'description': 'Those who treated sick livestock',
            'color': '#8e44ad',
            'icon': 'horse'
        },
        'touch_healing': {
            'name': 'Touch Healers',
            'description': 'Healing through physical contact',
            'color': '#f39c12',
            'icon': 'hand'
        },
        'charms_amulets': {
            'name': 'Charm Workers',
            'description': 'Using words, prayers, or objects for healing',
            'color': '#3498db',
            'icon': 'star'
        },
        'other': {
            'name': 'Other Healers',
            'description': 'Various folk healing practices',
            'color': '#95a5a6',
            'icon': 'circle'
        },
        'unspecified': {
            'name': 'Unspecified',
            'description': 'Healing type not recorded in detail',
            'color': '#bdc3c7',
            'icon': 'question'
        }
    }

    result = []
    for healing_type, healer_ids in clusters.items():
        info = cluster_info.get(healing_type, cluster_info['other'])
        result.append({
            'type': healing_type,
            'name': info['name'],
            'description': info['description'],
            'color': info['color'],
            'icon': info['icon'],
            'members': healer_ids,
            'count': len(healer_ids)
        })

    return sorted(result, key=lambda x: -x['count'])


def calculate_statistics(healers):
    """Calculate summary statistics for the network."""
    stats = {
        'total_healers': len(healers),
        'by_gender': defaultdict(int),
        'by_outcome': defaultdict(int),
        'by_healing_type': defaultdict(int),
        'by_economic_status': defaultdict(int),
        'age_distribution': [],
        'paradox_count': 0,
        'confession_rate': 0,
        'torture_rate': 0,
        'average_witnesses': 0,
        'total_victims': 0
    }

    ages = []
    confessed = 0
    tortured = 0
    total_witnesses = 0

    for healer in healers:
        stats['by_gender'][healer['gender'] or 'unknown'] += 1
        stats['by_outcome'][healer['outcome'] or 'unknown'] += 1
        stats['by_economic_status'][healer['economic_status'] or 'unknown'] += 1

        for ht in healer['healing_types']:
            stats['by_healing_type'][ht] += 1

        if healer['age']:
            ages.append(healer['age'])

        if healer['has_paradox']:
            stats['paradox_count'] += 1

        if healer['confessed']:
            confessed += 1

        if healer['torture_used']:
            tortured += 1

        total_witnesses += healer['witness_count']
        stats['total_victims'] += len(healer['victims'])

    if healers:
        stats['confession_rate'] = confessed / len(healers)
        stats['torture_rate'] = tortured / len(healers)
        stats['average_witnesses'] = total_witnesses / len(healers)

    if ages:
        stats['age_distribution'] = {
            'min': min(ages),
            'max': max(ages),
            'mean': sum(ages) / len(ages),
            'ages': sorted(ages)
        }

    # Convert defaultdicts to regular dicts for JSON
    stats['by_gender'] = dict(stats['by_gender'])
    stats['by_outcome'] = dict(stats['by_outcome'])
    stats['by_healing_type'] = dict(stats['by_healing_type'])
    stats['by_economic_status'] = dict(stats['by_economic_status'])

    return stats


def main():
    """Main function to build the healer network."""
    print("Extracting healer network from witch trial data...")

    all_healers = []
    trials_with_healers = 0
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

            trials_processed += 1
            healers = extract_healer_data(trial_data, trial_id)

            if healers:
                trials_with_healers += 1
                all_healers.extend(healers)

        except Exception as e:
            errors.append(f"{trial_id}: {str(e)}")
            print(f"Error processing {trial_id}: {e}")

    print(f"\nProcessed {trials_processed} trials")
    print(f"Found {trials_with_healers} trials with healers")
    print(f"Total healers: {len(all_healers)}")

    # Build network components
    edges = build_network_edges(all_healers)
    clusters = build_cluster_data(all_healers)
    statistics = calculate_statistics(all_healers)

    # Create output structure
    network = {
        'healers': all_healers,
        'edges': edges,
        'clusters': clusters,
        'statistics': statistics,
        'metadata': {
            'generated': datetime.now().isoformat(),
            'trials_processed': trials_processed,
            'trials_with_healers': trials_with_healers,
            'total_healers': len(all_healers),
            'total_edges': len(edges),
            'errors': errors[:10] if errors else []
        }
    }

    # Write output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(network, f, indent=2, ensure_ascii=False)

    print(f"\n=== Healer Network Extraction Complete ===")
    print(f"Output written to: {OUTPUT_FILE}")

    print(f"\n--- Cluster Summary ---")
    for cluster in clusters:
        print(f"  {cluster['name']}: {cluster['count']} healers")

    print(f"\n--- Key Statistics ---")
    print(f"  Paradox cases (healed then accused same person): {statistics['paradox_count']}")
    print(f"  Confession rate: {statistics['confession_rate']:.1%}")
    print(f"  Torture rate: {statistics['torture_rate']:.1%}")
    print(f"  Average witnesses per trial: {statistics['average_witnesses']:.1f}")

    print(f"\n--- Outcomes ---")
    for outcome, count in sorted(statistics['by_outcome'].items(), key=lambda x: -x[1]):
        print(f"  {outcome}: {count}")

    return network


if __name__ == '__main__':
    main()
