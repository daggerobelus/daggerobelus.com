#!/usr/bin/env python3
"""
Module 12-14: Visualization Suite for Lorraine Witchcraft Trials
Generates publication-quality figures for thesis.

Figures include:
- Network visualizations
- Centrality distributions
- Temporal evolution
- Model results
"""

import json
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path("/Users/natebaker/Desktop/analysis/2025/sna_pipeline")
NETWORK_DIR = BASE_DIR / "output/networks"
METRICS_DIR = BASE_DIR / "output/metrics"
ROLES_DIR = BASE_DIR / "output/roles"
MODELS_DIR = BASE_DIR / "output/models"
TEMPORAL_DIR = BASE_DIR / "output/temporal"
ROBUSTNESS_DIR = BASE_DIR / "output/robustness"
OUTPUT_DIR = BASE_DIR / "output/figures"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Publication style settings
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'serif',
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.figsize': (10, 8),
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})


class VisualizationSuite:
    """
    Generate publication-quality visualizations.
    """

    def __init__(self):
        self.G = None
        self.centrality_df = None

    def load_data(self):
        """Load all necessary data."""
        print("Loading data...")

        self.G = nx.read_graphml(NETWORK_DIR / "full_network.graphml")
        print(f"  Network: {self.G.number_of_nodes()} nodes")

        self.centrality_df = pd.read_csv(METRICS_DIR / "centrality_all_nodes.csv", index_col=0)
        print(f"  Centrality: {len(self.centrality_df)} nodes")

    def plot_degree_distribution(self):
        """Plot degree distribution (log-log scale)."""
        print("\n  Creating degree distribution plot...")

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Get degrees
        G_undirected = self.G.to_undirected()
        degrees = [d for n, d in G_undirected.degree()]

        # Histogram
        ax1 = axes[0]
        ax1.hist(degrees, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
        ax1.set_xlabel('Degree')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Degree Distribution')
        ax1.set_yscale('log')

        # Log-log plot
        ax2 = axes[1]
        degree_counts = pd.Series(degrees).value_counts().sort_index()
        ax2.scatter(degree_counts.index, degree_counts.values, alpha=0.6, s=30, color='steelblue')
        ax2.set_xlabel('Degree (log scale)')
        ax2.set_ylabel('Frequency (log scale)')
        ax2.set_title('Degree Distribution (Log-Log)')
        ax2.set_xscale('log')
        ax2.set_yscale('log')

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "fig1_degree_distribution.png")
        plt.savefig(OUTPUT_DIR / "fig1_degree_distribution.pdf")
        plt.close()

    def plot_centrality_comparison(self):
        """Plot centrality measure comparisons."""
        print("  Creating centrality comparison plot...")

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        df = self.centrality_df.copy()

        # Filter to nodes with some centrality
        df = df[df['degree'] > 0]

        # Degree vs Betweenness
        ax = axes[0, 0]
        ax.scatter(df['degree'], df['betweenness_centrality'],
                  alpha=0.3, s=10, color='steelblue')
        ax.set_xlabel('Degree')
        ax.set_ylabel('Betweenness Centrality')
        ax.set_title('Degree vs Betweenness')

        # Degree vs PageRank
        ax = axes[0, 1]
        ax.scatter(df['degree'], df['pagerank'],
                  alpha=0.3, s=10, color='forestgreen')
        ax.set_xlabel('Degree')
        ax.set_ylabel('PageRank')
        ax.set_title('Degree vs PageRank')

        # Betweenness vs Closeness
        ax = axes[1, 0]
        ax.scatter(df['betweenness_centrality'], df['closeness_centrality'],
                  alpha=0.3, s=10, color='coral')
        ax.set_xlabel('Betweenness Centrality')
        ax.set_ylabel('Closeness Centrality')
        ax.set_title('Betweenness vs Closeness')

        # Clustering vs Constraint
        ax = axes[1, 1]
        if 'clustering_coefficient' in df.columns and 'constraint' in df.columns:
            ax.scatter(df['clustering_coefficient'], df['constraint'],
                      alpha=0.3, s=10, color='purple')
            ax.set_xlabel('Clustering Coefficient')
            ax.set_ylabel('Constraint')
            ax.set_title('Clustering vs Constraint')

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "fig2_centrality_comparison.png")
        plt.savefig(OUTPUT_DIR / "fig2_centrality_comparison.pdf")
        plt.close()

    def plot_temporal_evolution(self):
        """Plot temporal evolution of the network."""
        print("  Creating temporal evolution plot...")

        # Load temporal metrics
        temporal_file = TEMPORAL_DIR / "temporal_network_metrics.csv"
        if not temporal_file.exists():
            print("    Skipping - no temporal data")
            return

        df = pd.read_csv(temporal_file)

        if len(df) == 0:
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Network size over time
        ax = axes[0, 0]
        x = range(len(df))
        ax.bar(x, df['n_nodes'], color='steelblue', alpha=0.7, label='Nodes')
        ax.set_xticks(x)
        ax.set_xticklabels(df['period'], rotation=45, ha='right')
        ax.set_xlabel('Time Period')
        ax.set_ylabel('Number of Nodes')
        ax.set_title('Network Size Over Time')

        # Edges over time
        ax = axes[0, 1]
        ax.bar(x, df['n_edges'], color='forestgreen', alpha=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels(df['period'], rotation=45, ha='right')
        ax.set_xlabel('Time Period')
        ax.set_ylabel('Number of Edges')
        ax.set_title('Connections Over Time')

        # Density over time
        ax = axes[1, 0]
        ax.plot(x, df['density'], 'o-', color='coral', markersize=8)
        ax.set_xticks(x)
        ax.set_xticklabels(df['period'], rotation=45, ha='right')
        ax.set_xlabel('Time Period')
        ax.set_ylabel('Network Density')
        ax.set_title('Density Over Time')

        # Clustering over time
        ax = axes[1, 1]
        if 'avg_clustering' in df.columns:
            ax.plot(x, df['avg_clustering'], 's-', color='purple', markersize=8)
            ax.set_xticks(x)
            ax.set_xticklabels(df['period'], rotation=45, ha='right')
            ax.set_xlabel('Time Period')
            ax.set_ylabel('Average Clustering')
            ax.set_title('Clustering Over Time')

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "fig3_temporal_evolution.png")
        plt.savefig(OUTPUT_DIR / "fig3_temporal_evolution.pdf")
        plt.close()

    def plot_accusation_waves(self):
        """Plot accusation waves over time."""
        print("  Creating accusation waves plot...")

        waves_file = TEMPORAL_DIR / "accusation_waves.csv"
        if not waves_file.exists():
            print("    Skipping - no wave data")
            return

        df = pd.read_csv(waves_file)
        df = df.sort_values('year')

        fig, ax = plt.subplots(figsize=(14, 6))

        ax.bar(df['year'], df['testimony'], color='darkred', alpha=0.7, label='Testimony Edges')
        ax.bar(df['year'], df['total_edges'] - df['testimony'], bottom=df['testimony'],
              color='steelblue', alpha=0.5, label='Other Edges')

        # Mark peak years
        median = df['total_edges'].median()
        peak_years = df[df['total_edges'] > median * 2]['year']
        for year in peak_years:
            ax.axvline(x=year, color='red', linestyle='--', alpha=0.3)

        ax.set_xlabel('Year')
        ax.set_ylabel('Number of Edges')
        ax.set_title('Accusation Waves: Testimony Activity by Year')
        ax.legend()

        # Add annotation for peak period
        ax.annotate('Peak Persecution\n(1596-1603)',
                   xy=(1600, df['total_edges'].max() * 0.8),
                   fontsize=10, ha='center',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "fig4_accusation_waves.png")
        plt.savefig(OUTPUT_DIR / "fig4_accusation_waves.pdf")
        plt.close()

    def plot_logistic_regression_results(self):
        """Plot logistic regression coefficients."""
        print("  Creating logistic regression results plot...")

        coef_file = MODELS_DIR / "accusation_coefficients.csv"
        if not coef_file.exists():
            print("    Skipping - no coefficient data")
            return

        df = pd.read_csv(coef_file)

        fig, ax = plt.subplots(figsize=(10, 6))

        # Sort by coefficient magnitude
        df = df.sort_values('coefficient')

        colors = ['forestgreen' if c > 0 else 'darkred' for c in df['coefficient']]

        bars = ax.barh(df['feature'], df['coefficient'], color=colors, alpha=0.7)

        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_xlabel('Coefficient (log-odds)')
        ax.set_ylabel('Feature')
        ax.set_title('Predictors of Accusation: Logistic Regression Coefficients')

        # Add odds ratio annotations
        for i, (coef, or_val) in enumerate(zip(df['coefficient'], df['odds_ratio'])):
            ax.annotate(f'OR={or_val:.2f}',
                       xy=(coef, i),
                       xytext=(5 if coef > 0 else -5, 0),
                       textcoords='offset points',
                       ha='left' if coef > 0 else 'right',
                       va='center',
                       fontsize=8)

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "fig5_logistic_regression.png")
        plt.savefig(OUTPUT_DIR / "fig5_logistic_regression.pdf")
        plt.close()

    def plot_network_sample(self, sample_size: int = 500):
        """Plot a sample of the network."""
        print("  Creating network sample visualization...")

        G_undirected = self.G.to_undirected()

        # Get largest connected component
        try:
            largest_cc = max(nx.connected_components(G_undirected), key=len)
            G_sub = G_undirected.subgraph(largest_cc).copy()
        except:
            G_sub = G_undirected

        # Sample if too large
        if G_sub.number_of_nodes() > sample_size:
            # Get top nodes by degree
            degrees = dict(G_sub.degree())
            top_nodes = sorted(degrees.keys(), key=lambda x: degrees[x], reverse=True)[:sample_size]
            G_sub = G_sub.subgraph(top_nodes).copy()

        # Layout
        pos = nx.spring_layout(G_sub, k=2, iterations=50, seed=42)

        # Node colors by degree
        degrees = dict(G_sub.degree())
        node_colors = [degrees[n] for n in G_sub.nodes()]

        fig, ax = plt.subplots(figsize=(14, 14))

        nodes = nx.draw_networkx_nodes(G_sub, pos,
                                       node_color=node_colors,
                                       node_size=[min(degrees[n] * 3, 200) for n in G_sub.nodes()],
                                       cmap=plt.cm.YlOrRd,
                                       alpha=0.7,
                                       ax=ax)

        nx.draw_networkx_edges(G_sub, pos, alpha=0.1, ax=ax)

        # Colorbar
        plt.colorbar(nodes, ax=ax, label='Degree', shrink=0.5)

        ax.set_title(f'Witch Trial Network Sample ({G_sub.number_of_nodes()} nodes, {G_sub.number_of_edges()} edges)')
        ax.axis('off')

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "fig6_network_visualization.png")
        plt.savefig(OUTPUT_DIR / "fig6_network_visualization.pdf")
        plt.close()

    def plot_robustness_summary(self):
        """Plot robustness check results."""
        print("  Creating robustness summary plot...")

        # Load bootstrap results
        bootstrap_file = ROBUSTNESS_DIR / "bootstrap_centrality_ranks.csv"
        if not bootstrap_file.exists():
            print("    Skipping - no robustness data")
            return

        df = pd.read_csv(bootstrap_file)

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Rank stability
        ax = axes[0]
        df_top = df.head(15)
        x = range(len(df_top))
        ax.errorbar(x, df_top['median_bootstrap_rank'],
                   yerr=[df_top['median_bootstrap_rank'] - df_top['rank_95ci_low'],
                         df_top['rank_95ci_high'] - df_top['median_bootstrap_rank']],
                   fmt='o', capsize=3, color='steelblue', markersize=8)
        ax.set_xticks(x)
        ax.set_xticklabels([n[:20] + '...' if len(n) > 20 else n for n in df_top['node']],
                          rotation=45, ha='right')
        ax.set_xlabel('Node')
        ax.set_ylabel('Bootstrap Rank (95% CI)')
        ax.set_title('Centrality Rank Stability')
        ax.invert_yaxis()

        # Load node removal sensitivity
        removal_file = ROBUSTNESS_DIR / "node_removal_sensitivity.csv"
        if removal_file.exists():
            removal_df = pd.read_csv(removal_file)

            ax = axes[1]
            ax.plot(removal_df['nodes_removed'], removal_df['fragmentation'],
                   'o-', color='darkred', markersize=8)
            ax.set_xlabel('Nodes Removed')
            ax.set_ylabel('Network Fragmentation')
            ax.set_title('Sensitivity to Node Removal')

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "fig7_robustness.png")
        plt.savefig(OUTPUT_DIR / "fig7_robustness.pdf")
        plt.close()

    def generate_summary_stats_table(self):
        """Generate summary statistics table."""
        print("  Creating summary statistics table...")

        G_undirected = self.G.to_undirected()

        stats = {
            'Network Metrics': {
                'Total Nodes': self.G.number_of_nodes(),
                'Total Edges': self.G.number_of_edges(),
                'Density': f"{nx.density(G_undirected):.6f}",
                'Average Degree': f"{2 * G_undirected.number_of_edges() / G_undirected.number_of_nodes():.2f}",
            }
        }

        # Add clustering
        try:
            stats['Network Metrics']['Avg Clustering'] = f"{nx.average_clustering(G_undirected):.3f}"
        except:
            pass

        # Add component info
        try:
            components = list(nx.connected_components(G_undirected))
            largest = max(components, key=len)
            stats['Network Metrics']['Components'] = len(components)
            stats['Network Metrics']['Largest Component'] = f"{len(largest)} ({100*len(largest)/G_undirected.number_of_nodes():.1f}%)"
        except:
            pass

        # Save as JSON
        with open(OUTPUT_DIR / "summary_statistics.json", 'w') as f:
            json.dump(stats, f, indent=2)

        # Save as text table
        with open(OUTPUT_DIR / "summary_statistics.txt", 'w') as f:
            f.write("LORRAINE WITCH TRIAL NETWORK: SUMMARY STATISTICS\n")
            f.write("=" * 50 + "\n\n")
            for category, metrics in stats.items():
                f.write(f"{category}\n")
                f.write("-" * 30 + "\n")
                for metric, value in metrics.items():
                    f.write(f"  {metric}: {value}\n")
                f.write("\n")

        print(f"    Saved summary_statistics.json and .txt")

    def run(self):
        """Generate all visualizations."""
        print("=" * 70)
        print("VISUALIZATION SUITE")
        print("=" * 70)

        self.load_data()

        print("\nGenerating figures...")
        self.plot_degree_distribution()
        self.plot_centrality_comparison()
        self.plot_temporal_evolution()
        self.plot_accusation_waves()
        self.plot_logistic_regression_results()
        self.plot_network_sample()
        self.plot_robustness_summary()
        self.generate_summary_stats_table()

        print("\n" + "=" * 70)
        print("VISUALIZATIONS COMPLETE")
        print("=" * 70)
        print(f"\nFigures saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    viz = VisualizationSuite()
    viz.run()
