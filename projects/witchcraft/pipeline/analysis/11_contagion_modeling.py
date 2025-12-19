#!/usr/bin/env python3
"""
Module 11: Contagion Modeling for Lorraine Witchcraft Trials
Models how accusations may have spread through social networks.

Research Questions:
- Did accusations spread like a contagion through social ties?
- What network positions were most vulnerable to accusation spread?
- How did kinship/witness networks facilitate accusation propagation?
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
OUTPUT_DIR = BASE_DIR / "output/contagion"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class ContagionModeler:
    """
    Model accusation spread as a network contagion process.
    """

    def __init__(self):
        self.G = None
        self.accused_set = set()
        self.witness_set = set()

    def load_data(self):
        """Load network data."""
        print("Loading data...")

        self.G = nx.read_graphml(NETWORK_DIR / "full_network.graphml")
        print(f"  Network: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")

        # Identify accused and witnesses from edges
        for u, v, data in self.G.edges(data=True):
            if data.get('relationship_type') == 'TESTIFIED_AGAINST':
                self.accused_set.add(v)
                self.witness_set.add(u)

        print(f"  Accused: {len(self.accused_set)}")
        print(f"  Witnesses: {len(self.witness_set)}")

    def compute_exposure_risk(self) -> pd.DataFrame:
        """Compute exposure to accused neighbors for each node."""
        print("\n=== Computing Exposure Risk ===")

        G_undirected = self.G.to_undirected()

        records = []
        for node in G_undirected.nodes():
            neighbors = list(G_undirected.neighbors(node))
            n_neighbors = len(neighbors)

            if n_neighbors == 0:
                continue

            # Count accused neighbors
            accused_neighbors = sum(1 for n in neighbors if n in self.accused_set)
            exposure_ratio = accused_neighbors / n_neighbors if n_neighbors > 0 else 0

            # Is this node accused?
            is_accused = node in self.accused_set

            records.append({
                'node': str(node)[:50],
                'n_neighbors': n_neighbors,
                'accused_neighbors': accused_neighbors,
                'exposure_ratio': exposure_ratio,
                'is_accused': int(is_accused),
            })

        df = pd.DataFrame(records)

        if len(df) > 0:
            # Analyze correlation between exposure and accusation
            correlation = df['exposure_ratio'].corr(df['is_accused'])

            print(f"  Nodes analyzed: {len(df)}")
            print(f"  Mean exposure ratio: {df['exposure_ratio'].mean():.3f}")
            print(f"  Correlation (exposure vs accusation): {correlation:.3f}")

            # Compare accused vs non-accused exposure
            accused_exposure = df[df['is_accused'] == 1]['exposure_ratio'].mean()
            nonaccused_exposure = df[df['is_accused'] == 0]['exposure_ratio'].mean()

            print(f"\n  Exposure by accusation status:")
            print(f"    Accused mean exposure: {accused_exposure:.3f}")
            print(f"    Non-accused mean exposure: {nonaccused_exposure:.3f}")
            print(f"    Ratio: {accused_exposure/nonaccused_exposure:.2f}x" if nonaccused_exposure > 0 else "")

        return df

    def simulate_cascade(self, seed_nodes: List[str], transmission_prob: float = 0.1,
                        max_steps: int = 10) -> Dict:
        """Simulate an accusation cascade from seed nodes."""
        G_undirected = self.G.to_undirected()

        infected = set(seed_nodes)
        susceptible = set(G_undirected.nodes()) - infected

        history = [{'step': 0, 'infected': len(infected), 'new_infections': len(infected)}]

        for step in range(1, max_steps + 1):
            new_infected = set()

            for node in susceptible:
                # Count infected neighbors
                neighbors = set(G_undirected.neighbors(node))
                infected_neighbors = len(neighbors & infected)

                if infected_neighbors > 0:
                    # Probability of infection
                    prob = 1 - (1 - transmission_prob) ** infected_neighbors
                    if np.random.random() < prob:
                        new_infected.add(node)

            infected.update(new_infected)
            susceptible -= new_infected

            history.append({
                'step': step,
                'infected': len(infected),
                'new_infections': len(new_infected)
            })

            if len(new_infected) == 0:
                break

        return {
            'final_infected': len(infected),
            'total_nodes': G_undirected.number_of_nodes(),
            'infection_rate': len(infected) / G_undirected.number_of_nodes(),
            'steps': len(history) - 1,
            'history': history,
        }

    def run_cascade_simulations(self, n_simulations: int = 50) -> pd.DataFrame:
        """Run multiple cascade simulations with different parameters."""
        print(f"\n=== Running Cascade Simulations ({n_simulations} per config) ===")

        G_undirected = self.G.to_undirected()
        all_nodes = list(G_undirected.nodes())

        # Get some actual early accused as potential seeds
        early_accused = list(self.accused_set)[:10]

        results = []

        # Different transmission probabilities
        for trans_prob in [0.05, 0.1, 0.15, 0.2]:
            for seed_size in [1, 3, 5, 10]:
                cascade_sizes = []

                for _ in range(n_simulations):
                    # Random seeds
                    seeds = list(np.random.choice(all_nodes, min(seed_size, len(all_nodes)),
                                                  replace=False))
                    result = self.simulate_cascade(seeds, transmission_prob=trans_prob)
                    cascade_sizes.append(result['final_infected'])

                results.append({
                    'transmission_prob': trans_prob,
                    'seed_size': seed_size,
                    'mean_cascade_size': np.mean(cascade_sizes),
                    'std_cascade_size': np.std(cascade_sizes),
                    'max_cascade_size': max(cascade_sizes),
                    'min_cascade_size': min(cascade_sizes),
                })

                print(f"  p={trans_prob}, seeds={seed_size}: "
                      f"mean cascade={np.mean(cascade_sizes):.0f} nodes")

        df = pd.DataFrame(results)
        return df

    def identify_superspreaders(self, top_n: int = 20) -> pd.DataFrame:
        """Identify nodes that could be superspreaders based on network position."""
        print(f"\n=== Identifying Potential Superspreaders ===")

        G_undirected = self.G.to_undirected()

        records = []

        for node in G_undirected.nodes():
            degree = G_undirected.degree(node)
            if degree < 5:
                continue

            # Get neighbors' degrees (reach)
            neighbors = list(G_undirected.neighbors(node))
            neighbor_degrees = [G_undirected.degree(n) for n in neighbors]
            avg_neighbor_degree = np.mean(neighbor_degrees) if neighbor_degrees else 0

            # Spreading potential = degree * avg neighbor degree
            spreading_potential = degree * avg_neighbor_degree

            # Is accused?
            is_accused = node in self.accused_set

            records.append({
                'node': str(node)[:50],
                'degree': degree,
                'avg_neighbor_degree': avg_neighbor_degree,
                'spreading_potential': spreading_potential,
                'is_accused': int(is_accused),
            })

        df = pd.DataFrame(records)

        if len(df) > 0:
            df = df.sort_values('spreading_potential', ascending=False)

            print(f"\n  Top {top_n} potential superspreaders:")
            for _, row in df.head(top_n).iterrows():
                accused_marker = " [ACCUSED]" if row['is_accused'] else ""
                print(f"    {row['node'][:40]}: potential={row['spreading_potential']:.0f}, "
                      f"degree={row['degree']:.0f}{accused_marker}")

        return df

    def analyze_accusation_chains(self) -> Dict:
        """Analyze chains of accusations (A accuses B, B accuses C)."""
        print("\n=== Analyzing Accusation Chains ===")

        # Build directed testimony graph
        testimony_G = nx.DiGraph()
        for u, v, data in self.G.edges(data=True):
            if data.get('relationship_type') == 'TESTIFIED_AGAINST':
                testimony_G.add_edge(u, v)

        # Find chains: witness becomes accused, then accuses others
        # A --testified--> B --testified--> C
        chains = []

        for node in testimony_G.nodes():
            # Node testified against someone
            targets = list(testimony_G.successors(node))
            # Node was accused by someone
            sources = list(testimony_G.predecessors(node))

            if targets and sources:
                # This node was both accused and an accuser
                chains.append({
                    'node': str(node)[:50],
                    'n_accused_by': len(sources),
                    'n_accused': len(targets),
                    'chain_role': 'transmitter'
                })

        print(f"  Accusation chain transmitters: {len(chains)}")

        if chains:
            # Sort by transmission (accused others)
            chains.sort(key=lambda x: x['n_accused'], reverse=True)
            print(f"\n  Top chain transmitters:")
            for chain in chains[:10]:
                print(f"    {chain['node'][:40]}: accused by {chain['n_accused_by']}, "
                      f"accused {chain['n_accused']} others")

        # Find longest paths
        longest_paths = []
        try:
            # Sample some paths
            for start in list(testimony_G.nodes())[:100]:
                for end in list(testimony_G.nodes())[:100]:
                    if start != end:
                        try:
                            path = nx.shortest_path(testimony_G, start, end)
                            if len(path) > 2:
                                longest_paths.append(len(path))
                        except nx.NetworkXNoPath:
                            pass
        except:
            pass

        path_stats = {
            'n_transmitters': len(chains),
            'max_path_length': max(longest_paths) if longest_paths else 0,
            'mean_path_length': np.mean(longest_paths) if longest_paths else 0,
        }

        if longest_paths:
            print(f"\n  Path statistics:")
            print(f"    Max accusation chain length: {max(longest_paths)}")
            print(f"    Mean chain length: {np.mean(longest_paths):.2f}")

        return {'chains': chains, 'path_stats': path_stats}

    def save_outputs(self, exposure_df: pd.DataFrame, cascade_df: pd.DataFrame,
                    superspreaders_df: pd.DataFrame, chain_results: Dict):
        """Save contagion analysis outputs."""
        print("\n=== Saving Outputs ===")

        # Save exposure analysis
        if len(exposure_df) > 0:
            exposure_df.to_csv(OUTPUT_DIR / "exposure_risk.csv", index=False)
            print(f"  Saved exposure_risk.csv")

        # Save cascade simulations
        if len(cascade_df) > 0:
            cascade_df.to_csv(OUTPUT_DIR / "cascade_simulations.csv", index=False)
            print(f"  Saved cascade_simulations.csv")

        # Save superspreaders
        if len(superspreaders_df) > 0:
            superspreaders_df.to_csv(OUTPUT_DIR / "superspreaders.csv", index=False)
            print(f"  Saved superspreaders.csv")

        # Save chain analysis
        if chain_results.get('chains'):
            chains_df = pd.DataFrame(chain_results['chains'])
            chains_df.to_csv(OUTPUT_DIR / "accusation_chains.csv", index=False)
            print(f"  Saved accusation_chains.csv")

        # Save summary
        summary = {
            'n_nodes_analyzed': len(exposure_df),
            'exposure_accusation_correlation': float(exposure_df['exposure_ratio'].corr(exposure_df['is_accused'])) if len(exposure_df) > 0 else 0,
            'n_superspreaders': len(superspreaders_df[superspreaders_df['degree'] >= 20]) if len(superspreaders_df) > 0 else 0,
            'n_chain_transmitters': len(chain_results.get('chains', [])),
            'max_chain_length': chain_results.get('path_stats', {}).get('max_path_length', 0),
        }

        with open(OUTPUT_DIR / "contagion_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"  Saved contagion_summary.json")

    def run(self):
        """Execute contagion modeling analysis."""
        print("=" * 70)
        print("CONTAGION MODELING ANALYSIS")
        print("=" * 70)

        # Load data
        self.load_data()

        # Run analyses
        exposure_df = self.compute_exposure_risk()
        cascade_df = self.run_cascade_simulations(n_simulations=30)
        superspreaders_df = self.identify_superspreaders()
        chain_results = self.analyze_accusation_chains()

        # Save outputs
        self.save_outputs(exposure_df, cascade_df, superspreaders_df, chain_results)

        print("\n" + "=" * 70)
        print("CONTAGION ANALYSIS COMPLETE")
        print("=" * 70)
        print(f"\nOutputs saved to: {OUTPUT_DIR}")

        return exposure_df, cascade_df


if __name__ == "__main__":
    modeler = ContagionModeler()
    modeler.run()
