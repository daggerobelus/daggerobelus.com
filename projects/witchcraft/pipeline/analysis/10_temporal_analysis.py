#!/usr/bin/env python3
"""
Module 10: Temporal Network Analysis for Lorraine Witchcraft Trials
Analyzes how the network evolved over time (1580s-1620s).

Research Questions:
- How did the network structure change over time?
- Were there "waves" of accusations?
- Did certain individuals become central at specific times?
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import networkx as nx
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path("/Users/natebaker/Desktop/analysis/2025/sna_pipeline")
NETWORK_DIR = BASE_DIR / "output/networks"
ENTITY_DIR = BASE_DIR / "output/entities"
EDGES_DIR = BASE_DIR / "output/edges"
OUTPUT_DIR = BASE_DIR / "output/temporal"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class TemporalAnalyzer:
    """
    Analyze temporal dynamics of the witch trial network.
    """

    def __init__(self):
        self.G = None
        self.edges_df = None
        self.year_networks = {}

    def load_data(self):
        """Load network and edge data with temporal information."""
        print("Loading data...")

        self.G = nx.read_graphml(NETWORK_DIR / "full_network.graphml")
        print(f"  Network: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")

        # Load edges with year information
        self.edges_df = pd.read_csv(EDGES_DIR / "all_edges.csv")
        print(f"  Edges with metadata: {len(self.edges_df)}")

        # Use temporal_marker column for year data
        if 'temporal_marker' in self.edges_df.columns:
            self.edges_df['year'] = pd.to_numeric(self.edges_df['temporal_marker'], errors='coerce')
            year_counts = self.edges_df['year'].dropna().value_counts().sort_index()
            print(f"  Years with data: {len(year_counts)}")
            if len(year_counts) > 0:
                print(f"  Year range: {int(self.edges_df['year'].min())} - {int(self.edges_df['year'].max())}")

    def build_temporal_networks(self, time_window: int = 5) -> Dict[str, nx.Graph]:
        """Build network snapshots by time window."""
        print(f"\n=== Building Temporal Networks (window={time_window} years) ===")

        if 'year' not in self.edges_df.columns:
            print("  No year information in edges - using full network")
            return {}

        # Filter to valid years
        edges_with_year = self.edges_df[self.edges_df['year'].notna()].copy()
        edges_with_year['year'] = edges_with_year['year'].astype(int)

        min_year = edges_with_year['year'].min()
        max_year = edges_with_year['year'].max()

        print(f"  Year range: {min_year}-{max_year}")
        print(f"  Edges with year data: {len(edges_with_year)}")

        # Create windows
        networks = {}
        for start in range(min_year, max_year + 1, time_window):
            end = start + time_window - 1
            window_edges = edges_with_year[
                (edges_with_year['year'] >= start) &
                (edges_with_year['year'] <= end)
            ]

            if len(window_edges) > 0:
                G = nx.Graph()
                for _, row in window_edges.iterrows():
                    G.add_edge(row['source'], row['target'])

                networks[f"{start}-{end}"] = G
                print(f"  {start}-{end}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        self.year_networks = networks
        return networks

    def compute_temporal_metrics(self) -> pd.DataFrame:
        """Compute network metrics for each time window."""
        print("\n=== Computing Temporal Metrics ===")

        if not self.year_networks:
            return pd.DataFrame()

        metrics = []

        for period, G in sorted(self.year_networks.items()):
            if G.number_of_nodes() == 0:
                continue

            # Basic metrics
            n_nodes = G.number_of_nodes()
            n_edges = G.number_of_edges()

            m = {
                'period': period,
                'n_nodes': n_nodes,
                'n_edges': n_edges,
                'density': nx.density(G) if n_nodes > 1 else 0,
                'avg_degree': 2 * n_edges / n_nodes if n_nodes > 0 else 0,
            }

            # Connected components
            if n_nodes > 0:
                try:
                    components = list(nx.connected_components(G))
                    m['n_components'] = len(components)
                    m['largest_component'] = len(max(components, key=len))
                    m['component_frac'] = m['largest_component'] / n_nodes
                except:
                    m['n_components'] = n_nodes
                    m['largest_component'] = 1
                    m['component_frac'] = 1 / n_nodes

            # Clustering
            try:
                m['avg_clustering'] = nx.average_clustering(G)
            except:
                m['avg_clustering'] = 0

            metrics.append(m)

        df = pd.DataFrame(metrics)

        if len(df) > 0:
            print("\n  Temporal evolution:")
            for _, row in df.iterrows():
                print(f"    {row['period']}: {row['n_nodes']:.0f} nodes, "
                      f"density={row['density']:.4f}, clustering={row['avg_clustering']:.3f}")

        return df

    def identify_temporal_hubs(self, top_n: int = 10) -> Dict[str, pd.DataFrame]:
        """Identify top central nodes in each time period."""
        print(f"\n=== Temporal Hub Analysis (top {top_n} per period) ===")

        if not self.year_networks:
            return {}

        period_hubs = {}

        for period, G in sorted(self.year_networks.items()):
            if G.number_of_nodes() < 5:
                continue

            # Compute centrality
            degree = dict(G.degree())
            try:
                betweenness = nx.betweenness_centrality(G)
            except:
                betweenness = {n: 0 for n in G.nodes()}

            # Get top nodes
            top_degree = sorted(degree.items(), key=lambda x: -x[1])[:top_n]
            top_between = sorted(betweenness.items(), key=lambda x: -x[1])[:top_n]

            hubs = []
            seen = set()
            for node, deg in top_degree:
                if node not in seen:
                    node_str = str(node)[:50] if node else 'unknown'
                    hubs.append({
                        'node': node_str,
                        'degree': deg,
                        'betweenness': betweenness.get(node, 0),
                        'rank_type': 'degree'
                    })
                    seen.add(node)

            for node, bet in top_between:
                if node not in seen:
                    node_str = str(node)[:50] if node else 'unknown'
                    hubs.append({
                        'node': node_str,
                        'degree': degree.get(node, 0),
                        'betweenness': bet,
                        'rank_type': 'betweenness'
                    })
                    seen.add(node)

            if hubs:
                period_hubs[period] = pd.DataFrame(hubs)
                print(f"\n  {period} top hubs:")
                for hub in hubs[:5]:
                    node_display = str(hub['node'])[:40]
                    print(f"    {node_display}: degree={hub['degree']}, "
                          f"betweenness={hub['betweenness']:.4f}")

        return period_hubs

    def analyze_accusation_waves(self) -> pd.DataFrame:
        """Analyze patterns in accusation timing."""
        print("\n=== Accusation Wave Analysis ===")

        if 'year' not in self.edges_df.columns:
            return pd.DataFrame()

        # Count edges by year
        yearly_counts = self.edges_df.groupby('year').agg({
            'source': 'count',
            'relationship_type': lambda x: x.value_counts().to_dict()
        }).reset_index()

        yearly_counts.columns = ['year', 'n_edges', 'edge_types']

        # Separate testimony edges
        testimony_counts = []
        for _, row in yearly_counts.iterrows():
            year = row['year']
            types = row['edge_types'] if isinstance(row['edge_types'], dict) else {}
            testimony_counts.append({
                'year': year,
                'total_edges': row['n_edges'],
                'testimony': types.get('TESTIFIED_AGAINST', 0),
                'co_witness': types.get('CO_WITNESS', 0),
                'kinship': types.get('SPOUSE_OF', 0) + types.get('WIDOW_OF', 0),
            })

        df = pd.DataFrame(testimony_counts)
        df = df.sort_values('year')

        # Identify peak years
        if len(df) > 0:
            median_edges = df['total_edges'].median()
            peak_years = df[df['total_edges'] > median_edges * 2]

            print(f"\n  Yearly edge counts (median={median_edges:.0f}):")
            for _, row in df.iterrows():
                marker = " *PEAK*" if row['total_edges'] > median_edges * 2 else ""
                print(f"    {int(row['year'])}: {int(row['total_edges'])} edges "
                      f"({int(row['testimony'])} testimony){marker}")

            if len(peak_years) > 0:
                print(f"\n  Peak years (>2x median): {list(peak_years['year'].astype(int))}")

        return df

    def track_node_careers(self, min_appearances: int = 3) -> pd.DataFrame:
        """Track how individuals' network positions changed over time."""
        print(f"\n=== Node Career Tracking (min {min_appearances} periods) ===")

        if not self.year_networks:
            return pd.DataFrame()

        # Track each node across periods
        node_careers = defaultdict(list)

        for period, G in sorted(self.year_networks.items()):
            degree = dict(G.degree())
            for node, deg in degree.items():
                if deg > 0:
                    node_careers[node].append({
                        'period': period,
                        'degree': deg,
                    })

        # Filter to those appearing in multiple periods
        careers = []
        for node, appearances in node_careers.items():
            if len(appearances) >= min_appearances:
                first_period = appearances[0]['period']
                last_period = appearances[-1]['period']
                max_degree = max(a['degree'] for a in appearances)
                node_str = str(node)[:50] if node else 'unknown'
                careers.append({
                    'node': node_str,
                    'n_periods': len(appearances),
                    'first_period': first_period,
                    'last_period': last_period,
                    'max_degree': max_degree,
                    'career_trajectory': 'rising' if appearances[-1]['degree'] > appearances[0]['degree']
                                        else 'falling' if appearances[-1]['degree'] < appearances[0]['degree']
                                        else 'stable'
                })

        df = pd.DataFrame(careers)

        if len(df) > 0:
            df = df.sort_values('n_periods', ascending=False)

            print(f"\n  Nodes appearing in {min_appearances}+ periods: {len(df)}")
            print(f"\n  Longest careers:")
            for _, row in df.head(10).iterrows():
                print(f"    {row['node'][:40]}: {row['n_periods']} periods "
                      f"({row['first_period']} to {row['last_period']}), "
                      f"trajectory={row['career_trajectory']}")

        return df

    def save_outputs(self, temporal_metrics: pd.DataFrame,
                    period_hubs: Dict[str, pd.DataFrame],
                    wave_analysis: pd.DataFrame,
                    careers: pd.DataFrame):
        """Save temporal analysis outputs."""
        print("\n=== Saving Outputs ===")

        # Save temporal metrics
        if len(temporal_metrics) > 0:
            temporal_metrics.to_csv(OUTPUT_DIR / "temporal_network_metrics.csv", index=False)
            print(f"  Saved temporal_network_metrics.csv")

        # Save hub analysis
        if period_hubs:
            all_hubs = []
            for period, df in period_hubs.items():
                df = df.copy()
                df['period'] = period
                all_hubs.append(df)
            combined_hubs = pd.concat(all_hubs, ignore_index=True)
            combined_hubs.to_csv(OUTPUT_DIR / "temporal_hubs.csv", index=False)
            print(f"  Saved temporal_hubs.csv")

        # Save wave analysis
        if len(wave_analysis) > 0:
            wave_analysis.to_csv(OUTPUT_DIR / "accusation_waves.csv", index=False)
            print(f"  Saved accusation_waves.csv")

        # Save careers
        if len(careers) > 0:
            careers.to_csv(OUTPUT_DIR / "node_careers.csv", index=False)
            print(f"  Saved node_careers.csv")

        # Save summary
        summary = {
            'n_time_periods': len(self.year_networks),
            'total_nodes_over_time': sum(G.number_of_nodes() for G in self.year_networks.values()),
            'n_long_career_nodes': len(careers) if len(careers) > 0 else 0,
        }

        if len(temporal_metrics) > 0:
            summary['peak_period'] = temporal_metrics.loc[
                temporal_metrics['n_edges'].idxmax(), 'period']
            summary['peak_edges'] = int(temporal_metrics['n_edges'].max())

        with open(OUTPUT_DIR / "temporal_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"  Saved temporal_summary.json")

    def run(self):
        """Execute temporal network analysis."""
        print("=" * 70)
        print("TEMPORAL NETWORK ANALYSIS")
        print("=" * 70)

        # Load data
        self.load_data()

        # Build temporal networks
        self.build_temporal_networks(time_window=5)

        # Analyze
        temporal_metrics = self.compute_temporal_metrics()
        period_hubs = self.identify_temporal_hubs()
        wave_analysis = self.analyze_accusation_waves()
        careers = self.track_node_careers(min_appearances=2)

        # Save
        self.save_outputs(temporal_metrics, period_hubs, wave_analysis, careers)

        print("\n" + "=" * 70)
        print("TEMPORAL ANALYSIS COMPLETE")
        print("=" * 70)
        print(f"\nOutputs saved to: {OUTPUT_DIR}")

        return temporal_metrics, period_hubs


if __name__ == "__main__":
    analyzer = TemporalAnalyzer()
    analyzer.run()
