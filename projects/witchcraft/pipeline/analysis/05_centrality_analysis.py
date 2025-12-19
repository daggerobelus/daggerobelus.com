#!/usr/bin/env python3
"""
Module 05: Centrality Analysis for Lorraine Witchcraft Trials
Computes comprehensive centrality metrics for power/authority analysis.

Metrics computed:
- Degree-based: degree, in/out-degree, weighted_degree
- Path-based: betweenness, closeness
- Eigenvector-based: eigenvector, PageRank
- Structural: clustering_coefficient, constraint
"""

import json
from pathlib import Path
from typing import Dict, Tuple
from collections import defaultdict
import pandas as pd
import numpy as np
import networkx as nx
import warnings
warnings.filterwarnings('ignore')

# Configuration
NETWORK_DIR = Path("/Users/natebaker/Desktop/analysis/sna_pipeline/output/networks")
ENTITY_DIR = Path("/Users/natebaker/Desktop/analysis/sna_pipeline/output/entities")
OUTPUT_DIR = Path("/Users/natebaker/Desktop/analysis/sna_pipeline/output/metrics")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class CentralityAnalyzer:
    """
    Compute comprehensive centrality metrics for network analysis.
    """

    def __init__(self):
        self.G = None
        self.G_undirected = None
        self.centrality_df = None

    def load_network(self) -> nx.Graph:
        """Load the constructed network."""
        print("Loading network...")

        # Load the full network
        self.G = nx.read_graphml(NETWORK_DIR / "full_network.graphml")
        print(f"  Loaded directed graph: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")

        # Create undirected version for some metrics
        self.G_undirected = self.G.to_undirected()
        print(f"  Undirected version: {self.G_undirected.number_of_edges()} edges")

        return self.G

    def compute_degree_centrality(self) -> pd.DataFrame:
        """Compute degree-based centrality metrics."""
        print("\n=== Computing Degree Centrality ===")

        metrics = {}

        # Basic degree (on undirected)
        degree = dict(self.G_undirected.degree())

        # Degree centrality (normalized)
        degree_centrality = nx.degree_centrality(self.G_undirected)

        # In-degree and out-degree (on directed)
        if self.G.is_directed():
            in_degree = dict(self.G.in_degree())
            out_degree = dict(self.G.out_degree())
        else:
            in_degree = degree
            out_degree = degree

        for node in self.G.nodes():
            metrics[node] = {
                'degree': degree.get(node, 0),
                'degree_centrality': degree_centrality.get(node, 0),
                'in_degree': in_degree.get(node, 0),
                'out_degree': out_degree.get(node, 0),
            }

        df = pd.DataFrame.from_dict(metrics, orient='index')
        print(f"  Degree range: {df['degree'].min()}-{df['degree'].max()}")
        print(f"  Average degree: {df['degree'].mean():.2f}")

        return df

    def compute_betweenness_centrality(self) -> pd.DataFrame:
        """Compute betweenness centrality (on largest component for efficiency)."""
        print("\n=== Computing Betweenness Centrality ===")

        # Use largest connected component for efficiency
        components = list(nx.connected_components(self.G_undirected))
        largest_cc = max(components, key=len)
        subgraph = self.G_undirected.subgraph(largest_cc)

        print(f"  Computing on largest component ({len(largest_cc)} nodes)...")

        # Compute betweenness (use approximation for large graphs)
        if len(largest_cc) > 1000:
            # Sample k nodes for approximation
            betweenness = nx.betweenness_centrality(subgraph, k=min(500, len(largest_cc)))
            print("  (Using approximation with k=500 samples)")
        else:
            betweenness = nx.betweenness_centrality(subgraph)

        # Add zeros for nodes not in largest component
        for node in self.G.nodes():
            if node not in betweenness:
                betweenness[node] = 0.0

        df = pd.DataFrame.from_dict(betweenness, orient='index', columns=['betweenness_centrality'])

        print(f"  Max betweenness: {df['betweenness_centrality'].max():.6f}")
        print(f"  Nodes with betweenness > 0: {(df['betweenness_centrality'] > 0).sum()}")

        return df

    def compute_closeness_centrality(self) -> pd.DataFrame:
        """Compute closeness centrality (on largest component)."""
        print("\n=== Computing Closeness Centrality ===")

        # Use largest connected component
        components = list(nx.connected_components(self.G_undirected))
        largest_cc = max(components, key=len)
        subgraph = self.G_undirected.subgraph(largest_cc)

        print(f"  Computing on largest component ({len(largest_cc)} nodes)...")

        closeness = nx.closeness_centrality(subgraph)

        # Add zeros for nodes not in largest component
        for node in self.G.nodes():
            if node not in closeness:
                closeness[node] = 0.0

        df = pd.DataFrame.from_dict(closeness, orient='index', columns=['closeness_centrality'])

        print(f"  Max closeness: {df['closeness_centrality'].max():.6f}")
        print(f"  Mean closeness (connected nodes): {df[df['closeness_centrality'] > 0]['closeness_centrality'].mean():.6f}")

        return df

    def compute_eigenvector_centrality(self) -> pd.DataFrame:
        """Compute eigenvector-based centrality metrics."""
        print("\n=== Computing Eigenvector Centrality ===")

        # Use largest connected component (eigenvector requires connected)
        components = list(nx.connected_components(self.G_undirected))
        largest_cc = max(components, key=len)
        subgraph = self.G_undirected.subgraph(largest_cc)

        print(f"  Computing on largest component ({len(largest_cc)} nodes)...")

        # Eigenvector centrality
        try:
            eigenvector = nx.eigenvector_centrality(subgraph, max_iter=500)
        except nx.PowerIterationFailedConvergence:
            print("  Warning: Eigenvector centrality did not converge, using numpy")
            eigenvector = nx.eigenvector_centrality_numpy(subgraph)

        # PageRank (works on full graph)
        pagerank = nx.pagerank(self.G_undirected, alpha=0.85, max_iter=200)

        # Initialize all nodes
        metrics = {}
        for node in self.G.nodes():
            metrics[node] = {
                'eigenvector_centrality': eigenvector.get(node, 0.0),
                'pagerank': pagerank.get(node, 0.0),
            }

        df = pd.DataFrame.from_dict(metrics, orient='index')

        print(f"  Max eigenvector: {df['eigenvector_centrality'].max():.6f}")
        print(f"  Max PageRank: {df['pagerank'].max():.6f}")

        return df

    def compute_clustering_coefficient(self) -> pd.DataFrame:
        """Compute local clustering coefficient."""
        print("\n=== Computing Clustering Coefficient ===")

        clustering = nx.clustering(self.G_undirected)

        df = pd.DataFrame.from_dict(clustering, orient='index', columns=['clustering_coefficient'])

        print(f"  Average clustering: {df['clustering_coefficient'].mean():.4f}")
        print(f"  Nodes with clustering > 0: {(df['clustering_coefficient'] > 0).sum()}")

        return df

    def compute_constraint(self) -> pd.DataFrame:
        """Compute Burt's constraint (structural holes measure)."""
        print("\n=== Computing Constraint (Structural Holes) ===")

        # Filter to nodes with degree >= 2
        subgraph_nodes = [n for n, d in self.G_undirected.degree() if d >= 2]
        subgraph = self.G_undirected.subgraph(subgraph_nodes)

        print(f"  Computing for {len(subgraph_nodes)} nodes with degree >= 2...")

        try:
            constraint = nx.constraint(subgraph)
        except:
            print("  Warning: Could not compute constraint, using zeros")
            constraint = {n: 0.0 for n in self.G.nodes()}

        # Add zeros for excluded nodes
        for node in self.G.nodes():
            if node not in constraint:
                constraint[node] = np.nan

        df = pd.DataFrame.from_dict(constraint, orient='index', columns=['constraint'])

        valid_constraint = df.dropna()
        if len(valid_constraint) > 0:
            print(f"  Average constraint: {valid_constraint['constraint'].mean():.4f}")
            print(f"  Nodes with low constraint (<0.5): {(valid_constraint['constraint'] < 0.5).sum()}")

        return df

    def merge_all_metrics(self, *dataframes) -> pd.DataFrame:
        """Merge all centrality metrics into single dataframe."""
        print("\n=== Merging All Metrics ===")

        # Start with first dataframe
        result = dataframes[0].copy()

        # Merge remaining
        for df in dataframes[1:]:
            result = result.join(df, how='outer')

        # Add node attributes
        for node in result.index:
            if node in self.G.nodes():
                attrs = self.G.nodes[node]
                for key in ['entity_type', 'gender', 'outcome', 'is_super_witness', 'became_accused']:
                    if key in attrs:
                        result.loc[node, key] = attrs[key]

        print(f"  Final dataframe: {len(result)} nodes x {len(result.columns)} metrics")

        return result

    def identify_top_central_nodes(self, df: pd.DataFrame, n: int = 20) -> Dict:
        """Identify top nodes by each centrality measure."""
        print(f"\n=== Top {n} Nodes by Centrality ===")

        results = {}

        numeric_cols = ['degree', 'betweenness_centrality', 'closeness_centrality',
                       'eigenvector_centrality', 'pagerank']

        for col in numeric_cols:
            if col in df.columns:
                top_nodes = df.nlargest(n, col)[col]
                results[col] = top_nodes.to_dict()

                print(f"\n  Top 5 by {col}:")
                for i, (node, value) in enumerate(list(top_nodes.items())[:5]):
                    print(f"    {i+1}. {node[:50]}: {value:.6f}")

        return results

    def compute_centrality_correlations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute correlations between centrality measures."""
        print("\n=== Centrality Correlations ===")

        numeric_cols = [col for col in df.columns if df[col].dtype in ['float64', 'int64']]
        corr = df[numeric_cols].corr()

        print("\nCorrelation matrix:")
        print(corr.round(3).to_string())

        return corr

    def analyze_super_witnesses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze centrality of super-witnesses specifically."""
        print("\n=== Super-Witness Centrality Analysis ===")

        # Filter to super-witnesses
        super_witnesses = df[df['is_super_witness'] == 'True'].copy()

        if len(super_witnesses) == 0:
            # Try boolean
            super_witnesses = df[df['is_super_witness'] == True].copy()

        print(f"  Found {len(super_witnesses)} super-witnesses")

        if len(super_witnesses) > 0:
            # Compare centrality of super-witnesses vs others
            others = df[~df.index.isin(super_witnesses.index)]

            numeric_cols = ['degree', 'betweenness_centrality', 'pagerank']

            print("\n  Mean centrality comparison:")
            for col in numeric_cols:
                if col in df.columns:
                    sw_mean = super_witnesses[col].mean()
                    other_mean = others[col].mean()
                    ratio = sw_mean / other_mean if other_mean > 0 else np.inf
                    print(f"    {col}: Super-witnesses={sw_mean:.4f}, Others={other_mean:.4f}, Ratio={ratio:.2f}x")

        return super_witnesses

    def save_outputs(self, df: pd.DataFrame, correlations: pd.DataFrame, top_nodes: Dict):
        """Save all analysis outputs."""
        print("\n=== Saving Outputs ===")

        # Save full centrality metrics
        df.to_csv(OUTPUT_DIR / "centrality_all_nodes.csv")
        print(f"  Saved centrality_all_nodes.csv ({len(df)} nodes)")

        # Save as JSON for easier loading
        df.to_json(OUTPUT_DIR / "centrality_all_nodes.json", orient='index')

        # Save correlations
        correlations.to_csv(OUTPUT_DIR / "centrality_correlations.csv")
        print(f"  Saved centrality_correlations.csv")

        # Save top nodes
        with open(OUTPUT_DIR / "top_central_nodes.json", 'w') as f:
            json.dump(top_nodes, f, indent=2)
        print(f"  Saved top_central_nodes.json")

        # Save summary statistics
        summary = df.describe()
        summary.to_csv(OUTPUT_DIR / "centrality_summary_stats.csv")
        print(f"  Saved centrality_summary_stats.csv")

    def run(self):
        """Execute the full centrality analysis pipeline."""
        print("=" * 70)
        print("CENTRALITY ANALYSIS PIPELINE")
        print("=" * 70)

        # Load network
        self.load_network()

        # Compute all centrality metrics
        degree_df = self.compute_degree_centrality()
        betweenness_df = self.compute_betweenness_centrality()
        closeness_df = self.compute_closeness_centrality()
        eigenvector_df = self.compute_eigenvector_centrality()
        clustering_df = self.compute_clustering_coefficient()
        constraint_df = self.compute_constraint()

        # Merge all metrics
        full_df = self.merge_all_metrics(
            degree_df, betweenness_df, closeness_df,
            eigenvector_df, clustering_df, constraint_df
        )

        # Analysis
        top_nodes = self.identify_top_central_nodes(full_df)
        correlations = self.compute_centrality_correlations(full_df)
        super_witness_analysis = self.analyze_super_witnesses(full_df)

        # Save outputs
        self.save_outputs(full_df, correlations, top_nodes)

        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE")
        print("=" * 70)
        print(f"\nComputed {len(full_df.columns)} metrics for {len(full_df)} nodes")
        print(f"Outputs saved to: {OUTPUT_DIR}")

        self.centrality_df = full_df
        return full_df


if __name__ == "__main__":
    analyzer = CentralityAnalyzer()
    centrality_df = analyzer.run()
