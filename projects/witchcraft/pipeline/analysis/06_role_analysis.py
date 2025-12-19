#!/usr/bin/env python3
"""
Module 06: Role Analysis for Lorraine Witchcraft Trials
Analyzes power structures: super-witnesses, brokerage positions, institutional influence.

Research Questions:
- Who were the super-witnesses appearing in 3+ trials?
- How did institutional actors shape prosecutions?
- What network positions predicted becoming accused?
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import pandas as pd
import numpy as np
import networkx as nx
import warnings
warnings.filterwarnings('ignore')

# Configuration
NETWORK_DIR = Path("/Users/natebaker/Desktop/analysis/2025/sna_pipeline/output/networks")
ENTITY_DIR = Path("/Users/natebaker/Desktop/analysis/2025/sna_pipeline/output/entities")
METRICS_DIR = Path("/Users/natebaker/Desktop/analysis/2025/sna_pipeline/output/metrics")
OUTPUT_DIR = Path("/Users/natebaker/Desktop/analysis/2025/sna_pipeline/output/roles")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class RoleAnalyzer:
    """
    Analyze structural positions and roles in the witch trial network.
    """

    def __init__(self):
        self.G = None
        self.centrality_df = None
        self.canonical_entities = None

    def load_data(self):
        """Load network and centrality data."""
        print("Loading data...")

        # Load network
        self.G = nx.read_graphml(NETWORK_DIR / "full_network.graphml")
        print(f"  Network: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")

        # Load centrality metrics
        self.centrality_df = pd.read_csv(METRICS_DIR / "centrality_all_nodes.csv", index_col=0)
        print(f"  Centrality metrics: {len(self.centrality_df)} nodes")

        # Load canonical entities
        with open(ENTITY_DIR / "canonical_entities.json") as f:
            self.canonical_entities = json.load(f)
        print(f"  Canonical entities: {len(self.canonical_entities)}")

    def identify_super_witnesses(self, min_trials: int = 3) -> pd.DataFrame:
        """Identify and analyze super-witnesses."""
        print(f"\n=== Super-Witness Analysis (>= {min_trials} trials) ===")

        super_witnesses = []

        for cid, entity in self.canonical_entities.items():
            appearances = entity.get('trial_appearances', [])
            witness_trials = [a for a in appearances if a.get('role') == 'witness']
            unique_trials = len(set(a.get('trial_id') for a in witness_trials))

            if unique_trials >= min_trials:
                # Get centrality metrics for this entity
                canonical_name = entity.get('canonical_name', cid)

                # Find matching row in centrality (try different name formats)
                centrality_row = None
                for potential_name in [canonical_name, cid]:
                    if potential_name in self.centrality_df.index:
                        centrality_row = self.centrality_df.loc[potential_name]
                        break

                sw_data = {
                    'canonical_id': cid,
                    'canonical_name': canonical_name,
                    'num_trials': unique_trials,
                    'gender': entity.get('gender', 'unknown'),
                    'became_accused': entity.get('attributes', {}).get('witness_to_accused', False),
                    'outcome': entity.get('outcome'),
                }

                # Add centrality if found
                if centrality_row is not None:
                    for col in ['degree', 'betweenness_centrality', 'pagerank', 'closeness_centrality']:
                        if col in centrality_row:
                            sw_data[col] = centrality_row[col]

                super_witnesses.append(sw_data)

        df = pd.DataFrame(super_witnesses)
        if len(df) > 0:
            df = df.sort_values('num_trials', ascending=False)

        print(f"\n  Found {len(df)} super-witnesses")
        print(f"  Total trial appearances: {df['num_trials'].sum()}")
        print(f"  Became accused: {df['became_accused'].sum()}")

        # Gender distribution
        print(f"\n  Gender distribution:")
        print(df['gender'].value_counts())

        return df

    def analyze_witness_to_accused_transitions(self) -> pd.DataFrame:
        """Detailed analysis of witness-to-accused transitions."""
        print("\n=== Witness-to-Accused Transition Analysis ===")

        transitions = []

        for cid, entity in self.canonical_entities.items():
            if entity.get('attributes', {}).get('witness_to_accused', False):
                appearances = entity.get('trial_appearances', [])

                witness_apps = [a for a in appearances if a.get('role') == 'witness']
                accused_apps = [a for a in appearances if a.get('role') == 'accused']

                if witness_apps and accused_apps:
                    # Get years
                    witness_years = [a.get('year') for a in witness_apps if a.get('year')]
                    accused_years = [a.get('year') for a in accused_apps if a.get('year')]

                    canonical_name = entity.get('canonical_name', cid)

                    # Get centrality
                    centrality_row = None
                    if canonical_name in self.centrality_df.index:
                        centrality_row = self.centrality_df.loc[canonical_name]

                    trans_data = {
                        'canonical_id': cid,
                        'canonical_name': canonical_name,
                        'num_witness_appearances': len(witness_apps),
                        'first_witness_year': min(witness_years) if witness_years else None,
                        'last_witness_year': max(witness_years) if witness_years else None,
                        'accused_year': min(accused_years) if accused_years else None,
                        'outcome': entity.get('outcome'),
                        'gender': entity.get('gender'),
                    }

                    if centrality_row is not None:
                        trans_data['degree'] = centrality_row.get('degree', 0)
                        trans_data['betweenness'] = centrality_row.get('betweenness_centrality', 0)

                    transitions.append(trans_data)

        df = pd.DataFrame(transitions)

        if len(df) > 0:
            print(f"\n  Found {len(df)} witness-to-accused transitions")

            # Analyze outcomes
            print(f"\n  Outcomes of transitioned individuals:")
            print(df['outcome'].value_counts())

            # Print details
            print(f"\n  Transition details:")
            for _, row in df.iterrows():
                print(f"    {row['canonical_name'][:40]}: {row['num_witness_appearances']} witness appearances "
                      f"-> accused -> {row['outcome']}")

        return df

    def compute_brokerage_scores(self) -> pd.DataFrame:
        """Compute simplified brokerage scores."""
        print("\n=== Brokerage Analysis ===")

        G_undirected = self.G.to_undirected()

        # Get nodes with sufficient degree
        nodes_to_analyze = [n for n, d in G_undirected.degree() if d >= 3]
        print(f"  Analyzing {len(nodes_to_analyze)} nodes with degree >= 3")

        brokerage_scores = []

        for node in nodes_to_analyze:
            neighbors = list(G_undirected.neighbors(node))
            degree = len(neighbors)

            # Count edges between neighbors (closure)
            neighbor_edges = 0
            possible_edges = 0
            for i, n1 in enumerate(neighbors):
                for n2 in neighbors[i+1:]:
                    possible_edges += 1
                    if G_undirected.has_edge(n1, n2):
                        neighbor_edges += 1

            # Brokerage = opportunities for bridging (non-redundant ties)
            if possible_edges > 0:
                closure_ratio = neighbor_edges / possible_edges
                brokerage = 1 - closure_ratio  # Higher = more bridging
            else:
                closure_ratio = 0
                brokerage = 0

            # Get node attributes
            node_attrs = self.G.nodes.get(node, {})

            brokerage_scores.append({
                'node': node,
                'degree': degree,
                'neighbor_edges': neighbor_edges,
                'possible_edges': possible_edges,
                'closure_ratio': closure_ratio,
                'brokerage_score': brokerage,
                'entity_type': node_attrs.get('entity_type', 'unknown'),
                'gender': node_attrs.get('gender', 'unknown'),
            })

        df = pd.DataFrame(brokerage_scores)

        if len(df) > 0:
            df = df.sort_values('brokerage_score', ascending=False)

            print(f"\n  Top 10 brokers:")
            for _, row in df.head(10).iterrows():
                print(f"    {row['node'][:40]}: brokerage={row['brokerage_score']:.3f}, "
                      f"degree={row['degree']}")

            print(f"\n  Average brokerage score: {df['brokerage_score'].mean():.3f}")
            print(f"  Nodes with high brokerage (>0.7): {(df['brokerage_score'] > 0.7).sum()}")

        return df

    def analyze_entity_type_centrality(self) -> pd.DataFrame:
        """Compare centrality across entity types."""
        print("\n=== Centrality by Entity Type ===")

        # Merge entity types with centrality
        df = self.centrality_df.copy()

        # Get entity types from graph
        for node in df.index:
            if node in self.G.nodes:
                df.loc[node, 'entity_type_graph'] = self.G.nodes[node].get('entity_type', 'unknown')

        # Group and compute means
        numeric_cols = ['degree', 'betweenness_centrality', 'pagerank', 'closeness_centrality']
        valid_cols = [c for c in numeric_cols if c in df.columns]

        if 'entity_type_graph' in df.columns:
            summary = df.groupby('entity_type_graph')[valid_cols].mean()

            print("\n  Mean centrality by entity type:")
            print(summary.round(4).to_string())

            return summary
        else:
            return pd.DataFrame()

    def save_outputs(self, super_witnesses: pd.DataFrame,
                    transitions: pd.DataFrame,
                    brokerage: pd.DataFrame,
                    type_centrality: pd.DataFrame):
        """Save all role analysis outputs."""
        print("\n=== Saving Outputs ===")

        # Save super-witnesses
        super_witnesses.to_csv(OUTPUT_DIR / "super_witnesses_analysis.csv", index=False)
        print(f"  Saved super_witnesses_analysis.csv ({len(super_witnesses)} rows)")

        # Save transitions
        transitions.to_csv(OUTPUT_DIR / "witness_to_accused_transitions.csv", index=False)
        print(f"  Saved witness_to_accused_transitions.csv ({len(transitions)} rows)")

        # Save brokerage
        brokerage.to_csv(OUTPUT_DIR / "brokerage_scores.csv", index=False)
        print(f"  Saved brokerage_scores.csv ({len(brokerage)} rows)")

        # Save type centrality
        if len(type_centrality) > 0:
            type_centrality.to_csv(OUTPUT_DIR / "centrality_by_entity_type.csv")
            print(f"  Saved centrality_by_entity_type.csv")

        # Save summary report
        summary = {
            'total_super_witnesses': len(super_witnesses),
            'super_witnesses_became_accused': int(super_witnesses['became_accused'].sum()) if 'became_accused' in super_witnesses.columns else 0,
            'total_transitions': len(transitions),
            'high_brokerage_nodes': int((brokerage['brokerage_score'] > 0.7).sum()) if len(brokerage) > 0 else 0,
        }

        with open(OUTPUT_DIR / "role_analysis_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"  Saved role_analysis_summary.json")

    def run(self):
        """Execute the full role analysis pipeline."""
        print("=" * 70)
        print("ROLE ANALYSIS PIPELINE")
        print("=" * 70)

        # Load data
        self.load_data()

        # Analyses
        super_witnesses = self.identify_super_witnesses(min_trials=3)
        transitions = self.analyze_witness_to_accused_transitions()
        brokerage = self.compute_brokerage_scores()
        type_centrality = self.analyze_entity_type_centrality()

        # Save outputs
        self.save_outputs(super_witnesses, transitions, brokerage, type_centrality)

        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE")
        print("=" * 70)
        print(f"\nOutputs saved to: {OUTPUT_DIR}")

        return super_witnesses, transitions, brokerage


if __name__ == "__main__":
    analyzer = RoleAnalyzer()
    super_witnesses, transitions, brokerage = analyzer.run()
