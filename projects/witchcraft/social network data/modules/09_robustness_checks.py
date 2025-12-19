#!/usr/bin/env python3
"""
Module 09: Robustness Checks for Lorraine Witchcraft Trials Analysis
Tests stability and reliability of findings through sensitivity analysis.

Checks:
- Bootstrap confidence intervals for centrality rankings
- Sensitivity to node removal (key figures)
- Edge weight threshold sensitivity
- Cross-validation stability of logistic regression
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import networkx as nx
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path("/Users/natebaker/Desktop/analysis/2025/sna_pipeline")
NETWORK_DIR = BASE_DIR / "output/networks"
METRICS_DIR = BASE_DIR / "output/metrics"
MODELS_DIR = BASE_DIR / "output/models"
OUTPUT_DIR = BASE_DIR / "output/robustness"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class RobustnessChecker:
    """
    Perform robustness checks on network analysis results.
    """

    def __init__(self):
        self.G = None
        self.centrality_df = None

    def load_data(self):
        """Load network and metrics data."""
        print("Loading data...")

        self.G = nx.read_graphml(NETWORK_DIR / "full_network.graphml")
        print(f"  Network: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")

        self.centrality_df = pd.read_csv(METRICS_DIR / "centrality_all_nodes.csv", index_col=0)
        print(f"  Centrality metrics: {len(self.centrality_df)} nodes")

    def bootstrap_centrality(self, n_bootstrap: int = 100, sample_frac: float = 0.8) -> Dict:
        """Bootstrap confidence intervals for centrality rankings."""
        print(f"\n=== Bootstrap Centrality Analysis ({n_bootstrap} iterations) ===")

        # Get top nodes by degree
        G_undirected = self.G.to_undirected()
        original_betweenness = nx.betweenness_centrality(G_undirected)
        top_nodes = sorted(original_betweenness.keys(),
                          key=lambda x: original_betweenness[x], reverse=True)[:20]

        # Store rank across bootstraps
        rank_results = {node: [] for node in top_nodes}

        edges = list(G_undirected.edges())
        n_sample = int(len(edges) * sample_frac)

        for i in range(n_bootstrap):
            if (i + 1) % 20 == 0:
                print(f"  Bootstrap iteration {i+1}/{n_bootstrap}")

            # Sample edges
            sampled_edges = np.random.choice(len(edges), n_sample, replace=True)
            G_sample = nx.Graph()
            for idx in sampled_edges:
                G_sample.add_edge(edges[idx][0], edges[idx][1])

            # Compute betweenness
            sample_betweenness = nx.betweenness_centrality(G_sample)

            # Get ranks for top nodes
            sorted_nodes = sorted(sample_betweenness.keys(),
                                 key=lambda x: sample_betweenness[x], reverse=True)

            for node in top_nodes:
                if node in sorted_nodes:
                    rank = sorted_nodes.index(node) + 1
                else:
                    rank = len(sorted_nodes) + 1
                rank_results[node].append(rank)

        # Summarize
        summary = []
        for node in top_nodes:
            ranks = rank_results[node]
            summary.append({
                'node': node[:50],
                'original_rank': top_nodes.index(node) + 1,
                'median_bootstrap_rank': np.median(ranks),
                'rank_95ci_low': np.percentile(ranks, 2.5),
                'rank_95ci_high': np.percentile(ranks, 97.5),
                'rank_stability': 1 - (np.std(ranks) / n_bootstrap),
            })

        df = pd.DataFrame(summary)
        print("\n  Top 10 nodes with bootstrap CIs:")
        for _, row in df.head(10).iterrows():
            print(f"    {row['node'][:40]}: rank {row['original_rank']:.0f} "
                  f"(95% CI: {row['rank_95ci_low']:.0f}-{row['rank_95ci_high']:.0f})")

        return df

    def node_removal_sensitivity(self, n_remove: int = 10) -> Dict:
        """Test sensitivity to removing high-degree nodes."""
        print(f"\n=== Node Removal Sensitivity (removing top {n_remove} nodes) ===")

        G_undirected = self.G.to_undirected()

        # Get top nodes by degree
        degrees = dict(G_undirected.degree())
        top_nodes = sorted(degrees.keys(), key=lambda x: degrees[x], reverse=True)[:n_remove]

        # Original metrics
        original = {
            'n_nodes': G_undirected.number_of_nodes(),
            'n_edges': G_undirected.number_of_edges(),
            'density': nx.density(G_undirected),
            'avg_clustering': nx.average_clustering(G_undirected),
        }

        # Try to get largest component
        try:
            largest_cc = max(nx.connected_components(G_undirected), key=len)
            original['largest_component'] = len(largest_cc)
        except:
            original['largest_component'] = 0

        print(f"\n  Original network:")
        for k, v in original.items():
            print(f"    {k}: {v:.4f}" if isinstance(v, float) else f"    {k}: {v}")

        # Remove nodes one by one
        results = []
        G_current = G_undirected.copy()

        for i, node in enumerate(top_nodes):
            if node not in G_current:
                continue

            # Remove node
            G_current.remove_node(node)

            metrics = {
                'removed_node': node[:50],
                'nodes_removed': i + 1,
                'n_nodes': G_current.number_of_nodes(),
                'n_edges': G_current.number_of_edges(),
                'density': nx.density(G_current) if G_current.number_of_nodes() > 1 else 0,
                'avg_clustering': nx.average_clustering(G_current) if G_current.number_of_nodes() > 0 else 0,
            }

            try:
                largest_cc = max(nx.connected_components(G_current), key=len)
                metrics['largest_component'] = len(largest_cc)
                metrics['fragmentation'] = 1 - (len(largest_cc) / G_current.number_of_nodes())
            except:
                metrics['largest_component'] = 0
                metrics['fragmentation'] = 1.0

            results.append(metrics)

        df = pd.DataFrame(results)

        # Report impact
        print(f"\n  After removing {n_remove} top nodes:")
        final = df.iloc[-1]
        print(f"    Nodes remaining: {final['n_nodes']} ({100*final['n_nodes']/original['n_nodes']:.1f}%)")
        print(f"    Edges remaining: {final['n_edges']} ({100*final['n_edges']/original['n_edges']:.1f}%)")
        print(f"    Fragmentation: {final['fragmentation']:.3f}")

        return df, original

    def logistic_regression_cv_stability(self, n_repeats: int = 10) -> Dict:
        """Test cross-validation stability across random splits."""
        print(f"\n=== Logistic Regression CV Stability ({n_repeats} repeats) ===")

        # Load model data
        model_data = pd.read_csv(MODELS_DIR / "accusation_model_data.csv")

        feature_cols = ['degree', 'betweenness_centrality', 'pagerank',
                       'closeness_centrality', 'eigenvector_centrality',
                       'clustering_coefficient', 'brokerage_score',
                       'gender_female', 'gender_male']

        # Filter to valid columns
        valid_cols = [c for c in feature_cols if c in model_data.columns]
        X = model_data[valid_cols].fillna(0).values
        y = model_data['is_accused'].values

        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Run multiple CV iterations
        auc_scores = []
        coef_stability = {col: [] for col in valid_cols}

        for i in range(n_repeats):
            model = LogisticRegression(
                penalty='l2', C=1.0,
                class_weight='balanced',
                max_iter=1000,
                random_state=i
            )

            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=i)
            cv_auc = cross_val_score(model, X_scaled, y, cv=cv, scoring='roc_auc')
            auc_scores.extend(cv_auc)

            # Fit full model for coefficients
            model.fit(X_scaled, y)
            for j, col in enumerate(valid_cols):
                coef_stability[col].append(model.coef_[0][j])

        # Summarize
        print(f"\n  AUC across {n_repeats * 5} CV folds:")
        print(f"    Mean: {np.mean(auc_scores):.3f}")
        print(f"    Std: {np.std(auc_scores):.3f}")
        print(f"    Min: {np.min(auc_scores):.3f}")
        print(f"    Max: {np.max(auc_scores):.3f}")

        print(f"\n  Coefficient stability (CV across random seeds):")
        coef_summary = []
        for col in valid_cols:
            coefs = coef_stability[col]
            sign_consistency = np.mean(np.sign(coefs) == np.sign(np.mean(coefs)))
            coef_summary.append({
                'feature': col,
                'mean_coef': np.mean(coefs),
                'std_coef': np.std(coefs),
                'sign_consistency': sign_consistency,
            })
            print(f"    {col:30s}: {np.mean(coefs):+.4f} +/- {np.std(coefs):.4f} "
                  f"(sign stable: {sign_consistency:.0%})")

        results = {
            'auc_mean': float(np.mean(auc_scores)),
            'auc_std': float(np.std(auc_scores)),
            'auc_min': float(np.min(auc_scores)),
            'auc_max': float(np.max(auc_scores)),
            'n_cv_folds': len(auc_scores),
            'coefficient_summary': coef_summary,
        }

        return results

    def edge_type_sensitivity(self) -> Dict:
        """Test how results change with different edge types included."""
        print("\n=== Edge Type Sensitivity Analysis ===")

        # Count edges by type
        edge_types = {}
        for u, v, data in self.G.edges(data=True):
            et = data.get('relationship_type', 'unknown')
            edge_types[et] = edge_types.get(et, 0) + 1

        print(f"\n  Edge types in network:")
        for et, count in sorted(edge_types.items(), key=lambda x: -x[1]):
            print(f"    {et}: {count}")

        results = []

        # Test different edge type combinations
        edge_configs = [
            ('testimony_only', ['TESTIFIED_AGAINST']),
            ('testimony_co_witness', ['TESTIFIED_AGAINST', 'CO_WITNESS']),
            ('testimony_kinship', ['TESTIFIED_AGAINST', 'SPOUSE_OF', 'WIDOW_OF', 'CHILD_OF']),
            ('all_types', list(edge_types.keys())),
        ]

        for config_name, included_types in edge_configs:
            # Create subgraph
            edges = [(u, v) for u, v, d in self.G.edges(data=True)
                    if d.get('relationship_type') in included_types]

            G_sub = nx.Graph()
            G_sub.add_edges_from(edges)

            if G_sub.number_of_nodes() == 0:
                continue

            # Compute metrics
            metrics = {
                'config': config_name,
                'n_nodes': G_sub.number_of_nodes(),
                'n_edges': G_sub.number_of_edges(),
                'density': nx.density(G_sub),
                'avg_degree': 2 * G_sub.number_of_edges() / G_sub.number_of_nodes(),
            }

            try:
                largest_cc = max(nx.connected_components(G_sub), key=len)
                metrics['largest_component_frac'] = len(largest_cc) / G_sub.number_of_nodes()
            except:
                metrics['largest_component_frac'] = 0

            results.append(metrics)
            print(f"\n  {config_name}:")
            for k, v in metrics.items():
                if k != 'config':
                    print(f"    {k}: {v:.4f}" if isinstance(v, float) else f"    {k}: {v}")

        return pd.DataFrame(results)

    def common_name_ambiguity_analysis(self) -> Dict:
        """Analyze potential misattribution due to common names like 'Jean', 'Marie'."""
        print("\n=== Common Name Ambiguity Analysis ===")

        # Common Early Modern French names that may conflate different individuals
        COMMON_NAMES = ['jean', 'marie', 'catherine', 'marguerite', 'nicolas',
                       'claude', 'pierre', 'didier', 'mengeon', 'barbe',
                       'jeanne', 'claudon', 'jennon', 'mengeatte']

        # Analyze nodes
        node_names = list(self.G.nodes())

        # Find nodes that are just common first names (high ambiguity risk)
        ambiguous_nodes = []
        for node in node_names:
            node_lower = node.lower().strip()
            # Check if node is just a common name with no qualifier
            for common in COMMON_NAMES:
                if node_lower == common or node_lower.startswith(common + ' ') and len(node_lower.split()) == 1:
                    ambiguous_nodes.append({
                        'node': node,
                        'matched_name': common,
                        'degree': self.G.degree(node),
                        'risk_level': 'high' if self.G.degree(node) > 20 else 'medium',
                    })
                    break

        print(f"\n  Potentially ambiguous nodes (common names only): {len(ambiguous_nodes)}")

        # Sort by degree (higher degree = more risk of conflation)
        ambiguous_df = pd.DataFrame(ambiguous_nodes)
        if len(ambiguous_df) > 0:
            ambiguous_df = ambiguous_df.sort_values('degree', ascending=False)

            print(f"\n  Top 10 highest-risk ambiguous nodes:")
            for _, row in ambiguous_df.head(10).iterrows():
                print(f"    '{row['node']}': degree={row['degree']}, risk={row['risk_level']}")

        # Count name frequency
        name_counts = {}
        for node in node_names:
            for common in COMMON_NAMES:
                if common in node.lower():
                    name_counts[common] = name_counts.get(common, 0) + 1

        print(f"\n  Common name frequencies in network:")
        for name, count in sorted(name_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"    {name}: {count} nodes")

        # Sensitivity: What if we removed ambiguous high-degree nodes?
        print("\n  Sensitivity test: Impact of removing high-degree ambiguous nodes")
        G_test = self.G.to_undirected()
        original_edges = G_test.number_of_edges()
        original_nodes = G_test.number_of_nodes()

        if len(ambiguous_df) > 0:
            high_risk = ambiguous_df[ambiguous_df['degree'] > 20]
            for node in high_risk['node']:
                if node in G_test:
                    G_test.remove_node(node)

            print(f"    Removed {len(high_risk)} high-risk ambiguous nodes")
            print(f"    Nodes: {G_test.number_of_nodes()} ({100*G_test.number_of_nodes()/original_nodes:.1f}% remaining)")
            print(f"    Edges: {G_test.number_of_edges()} ({100*G_test.number_of_edges()/original_edges:.1f}% remaining)")

        results = {
            'n_ambiguous_nodes': len(ambiguous_nodes),
            'n_high_risk': len(ambiguous_df[ambiguous_df['degree'] > 20]) if len(ambiguous_df) > 0 else 0,
            'common_name_counts': name_counts,
            'pct_nodes_remaining_after_removal': 100 * G_test.number_of_nodes() / original_nodes if original_nodes > 0 else 0,
            'pct_edges_remaining_after_removal': 100 * G_test.number_of_edges() / original_edges if original_edges > 0 else 0,
            'ambiguous_nodes': ambiguous_df.to_dict('records') if len(ambiguous_df) > 0 else [],
        }

        return results, ambiguous_df if len(ambiguous_df) > 0 else pd.DataFrame()

    def permutation_test_gender(self, n_permutations: int = 1000) -> Dict:
        """Permutation test for gender effects on accusation."""
        print(f"\n=== Permutation Test for Gender Effect ({n_permutations} permutations) ===")

        # Load model data
        model_data = pd.read_csv(MODELS_DIR / "accusation_model_data.csv")

        # Calculate observed gender difference in accusation rates
        female = model_data[model_data['gender_female'] == 1]
        male = model_data[model_data['gender_male'] == 1]

        female_rate = female['is_accused'].mean() if len(female) > 0 else 0
        male_rate = male['is_accused'].mean() if len(male) > 0 else 0
        observed_diff = female_rate - male_rate

        print(f"\n  Observed accusation rates:")
        print(f"    Female: {female_rate:.3f} ({len(female)} individuals)")
        print(f"    Male: {male_rate:.3f} ({len(male)} individuals)")
        print(f"    Difference: {observed_diff:+.3f}")

        # Permutation test
        combined = pd.concat([female, male])
        if len(combined) < 10:
            print("  Insufficient data for permutation test")
            return {}

        perm_diffs = []
        accused = combined['is_accused'].values
        n_female = len(female)

        for _ in range(n_permutations):
            # Shuffle accused status
            shuffled = np.random.permutation(accused)
            perm_female_rate = shuffled[:n_female].mean()
            perm_male_rate = shuffled[n_female:].mean()
            perm_diffs.append(perm_female_rate - perm_male_rate)

        # Calculate p-value
        p_value = np.mean(np.abs(perm_diffs) >= np.abs(observed_diff))

        print(f"\n  Permutation test results:")
        print(f"    p-value (two-tailed): {p_value:.4f}")
        if p_value < 0.05:
            print("    SIGNIFICANT: Gender effect unlikely due to chance")
        else:
            print("    NOT significant: Gender effect could be due to chance")

        results = {
            'female_rate': float(female_rate),
            'male_rate': float(male_rate),
            'observed_diff': float(observed_diff),
            'p_value': float(p_value),
            'n_permutations': n_permutations,
        }

        return results

    def save_outputs(self, bootstrap_df: pd.DataFrame, removal_df: pd.DataFrame,
                    original_metrics: Dict, cv_results: Dict,
                    edge_sensitivity: pd.DataFrame, gender_perm: Dict,
                    name_ambiguity: Dict, ambiguous_df: pd.DataFrame):
        """Save all robustness check outputs."""
        print("\n=== Saving Outputs ===")

        # Save bootstrap results
        bootstrap_df.to_csv(OUTPUT_DIR / "bootstrap_centrality_ranks.csv", index=False)
        print(f"  Saved bootstrap_centrality_ranks.csv")

        # Save node removal results
        removal_df.to_csv(OUTPUT_DIR / "node_removal_sensitivity.csv", index=False)
        print(f"  Saved node_removal_sensitivity.csv")

        # Save edge sensitivity
        edge_sensitivity.to_csv(OUTPUT_DIR / "edge_type_sensitivity.csv", index=False)
        print(f"  Saved edge_type_sensitivity.csv")

        # Save ambiguous nodes
        if len(ambiguous_df) > 0:
            ambiguous_df.to_csv(OUTPUT_DIR / "ambiguous_common_names.csv", index=False)
            print(f"  Saved ambiguous_common_names.csv")

        # Save combined results
        all_results = {
            'bootstrap_analysis': {
                'n_iterations': 30,
                'sample_fraction': 0.8,
                'top_10_rank_stability': float(bootstrap_df.head(10)['rank_stability'].mean()),
            },
            'node_removal': {
                'original_metrics': original_metrics,
                'fragmentation_after_10': float(removal_df.iloc[-1]['fragmentation']),
            },
            'cv_stability': cv_results,
            'gender_permutation_test': gender_perm,
            'common_name_ambiguity': {
                'n_ambiguous_nodes': name_ambiguity.get('n_ambiguous_nodes', 0),
                'n_high_risk': name_ambiguity.get('n_high_risk', 0),
                'common_name_counts': name_ambiguity.get('common_name_counts', {}),
                'pct_network_after_removal': name_ambiguity.get('pct_edges_remaining_after_removal', 100),
            },
        }

        with open(OUTPUT_DIR / "robustness_summary.json", 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"  Saved robustness_summary.json")

    def run(self):
        """Execute all robustness checks."""
        print("=" * 70)
        print("ROBUSTNESS CHECKS PIPELINE")
        print("=" * 70)

        # Load data
        self.load_data()

        # Run checks
        bootstrap_df = self.bootstrap_centrality(n_bootstrap=30)  # Reduced for speed
        removal_df, original_metrics = self.node_removal_sensitivity(n_remove=10)
        cv_results = self.logistic_regression_cv_stability(n_repeats=10)
        edge_sensitivity = self.edge_type_sensitivity()
        name_ambiguity, ambiguous_df = self.common_name_ambiguity_analysis()
        gender_perm = self.permutation_test_gender(n_permutations=500)  # Reduced for speed

        # Save outputs
        self.save_outputs(bootstrap_df, removal_df, original_metrics,
                         cv_results, edge_sensitivity, gender_perm,
                         name_ambiguity, ambiguous_df)

        print("\n" + "=" * 70)
        print("ROBUSTNESS CHECKS COMPLETE")
        print("=" * 70)
        print(f"\nOutputs saved to: {OUTPUT_DIR}")

        return {
            'bootstrap': bootstrap_df,
            'removal': removal_df,
            'cv': cv_results,
            'edge_sensitivity': edge_sensitivity,
        }


if __name__ == "__main__":
    checker = RobustnessChecker()
    checker.run()
