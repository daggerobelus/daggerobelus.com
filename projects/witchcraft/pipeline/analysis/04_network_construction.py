#!/usr/bin/env python3
"""
Module 04: Network Construction for Lorraine Witchcraft Trials
Builds multi-layer NetworkX graph from extracted entities and edges.

Features:
- Multi-layer network (separate layers by relationship type)
- Node attributes (entity type, gender, outcomes)
- Edge attributes (confidence, evidence, temporal markers)
- Graph export to GraphML for visualization tools
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import pandas as pd
import numpy as np
import networkx as nx
import warnings
warnings.filterwarnings('ignore')

# Configuration
ENTITY_DIR = Path("/Users/natebaker/Desktop/analysis/sna_pipeline/output/entities")
EDGE_DIR = Path("/Users/natebaker/Desktop/analysis/sna_pipeline/output/edges")
OUTPUT_DIR = Path("/Users/natebaker/Desktop/analysis/sna_pipeline/output/networks")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class WitchcraftNetwork:
    """
    Multi-layer temporal network for witchcraft trials analysis.
    """

    # Relationship type to layer mapping
    LAYERS = {
        'kinship': ['SPOUSE_OF', 'WIDOW_OF', 'CHILD_OF', 'SIBLING_OF'],
        'accusation': ['TESTIFIED_AGAINST', 'NAMED_AS_WITCH', 'SEEN_AT_SABBAT'],
        'conflict': ['QUARRELED_WITH', 'THREATENED'],
        'co_presence': ['CO_ACCUSED', 'CO_WITNESS'],
        'institutional': ['JUDGED_BY'],
    }

    def __init__(self):
        self.G = nx.MultiDiGraph()  # Main graph (directed multigraph)
        self.node_attributes = {}
        self.edge_count = 0

    def load_data(self) -> Tuple[Dict, List[Dict]]:
        """Load canonical entities and edges."""
        print("Loading data...")

        # Load canonical entities
        with open(ENTITY_DIR / "canonical_entities.json") as f:
            entities = json.load(f)
        print(f"  Loaded {len(entities)} canonical entities")

        # Load edges
        with open(EDGE_DIR / "all_edges.json") as f:
            edges = json.load(f)
        print(f"  Loaded {len(edges)} edges")

        return entities, edges

    def build_node_index(self, entities: Dict, edges: List[Dict]) -> Dict[str, Dict]:
        """Build comprehensive node index from entities and edge endpoints."""
        print("\n=== Building Node Index ===")

        nodes = {}

        # Add canonical entities as nodes
        for cid, entity in entities.items():
            canonical_name = entity.get('canonical_name', cid)
            nodes[canonical_name] = {
                'canonical_id': cid,
                'entity_type': entity.get('entity_type', 'person'),
                'gender': entity.get('gender', 'unknown'),
                'outcome': entity.get('outcome'),
                'locations': entity.get('locations', []),
                'num_trial_appearances': len(entity.get('trial_appearances', [])),
                'is_super_witness': len([a for a in entity.get('trial_appearances', [])
                                        if a.get('role') == 'witness']) >= 3,
                'became_accused': entity.get('attributes', {}).get('witness_to_accused', False),
            }

        # Add any nodes from edges that aren't in entities
        edge_nodes = set()
        testimony_sources = set()  # Track witnesses (sources of TESTIFIED_AGAINST)
        testimony_targets = set()  # Track accused (targets of TESTIFIED_AGAINST)

        for edge in edges:
            src = edge.get('source', '')
            tgt = edge.get('target', '')
            rel_type = edge.get('relationship_type', '')

            if src and isinstance(src, str) and src.strip():
                edge_nodes.add(src)
                if rel_type == 'TESTIFIED_AGAINST':
                    testimony_sources.add(src)

            if tgt and isinstance(tgt, str) and tgt.strip():
                edge_nodes.add(tgt)
                if rel_type == 'TESTIFIED_AGAINST':
                    testimony_targets.add(tgt)

        # Remove empty strings and None
        edge_nodes.discard('')
        edge_nodes.discard(None)

        # Add missing nodes with inferred attributes
        for node in edge_nodes:
            if node not in nodes:
                # Infer entity type from node ID and edge relationships
                # 1. Check if node ID contains "witch" (case insensitive) -> accused
                # 2. Check if node is target of TESTIFIED_AGAINST -> accused
                # 3. Check if node is source of TESTIFIED_AGAINST -> witness
                if re.search(r'\bwitch\b', node, re.IGNORECASE) or node in testimony_targets:
                    entity_type = 'accused'
                elif node in testimony_sources:
                    entity_type = 'witness'
                else:
                    entity_type = 'unknown'

                nodes[node] = {
                    'entity_type': entity_type,
                    'gender': 'unknown',
                    'outcome': None,
                    'locations': [],
                    'num_trial_appearances': 1,
                    'is_super_witness': False,
                    'became_accused': False,
                }

        print(f"  Created index with {len(nodes)} nodes")
        print(f"    From entities: {len(entities)}")
        print(f"    From edges: {len(edge_nodes)}")

        return nodes

    def add_nodes_to_graph(self, nodes: Dict[str, Dict]):
        """Add all nodes to the graph with their attributes."""
        print("\n=== Adding Nodes to Graph ===")

        skipped = 0
        for name, attrs in nodes.items():
            # Skip None or empty names
            if name is None or name == '' or (isinstance(name, str) and not name.strip()):
                skipped += 1
                continue
            self.G.add_node(name, **attrs)

        self.node_attributes = {k: v for k, v in nodes.items() if k and k.strip()}
        print(f"  Added {self.G.number_of_nodes()} nodes (skipped {skipped} invalid)")

    def add_edges_to_graph(self, edges: List[Dict]):
        """Add all edges to the graph."""
        print("\n=== Adding Edges to Graph ===")

        edge_counts = defaultdict(int)

        for edge in edges:
            source = edge.get('source', '')
            target = edge.get('target', '')
            rel_type = edge.get('relationship_type', 'UNKNOWN')

            if not source or not target:
                continue

            # Determine layer
            layer = 'other'
            for layer_name, types in self.LAYERS.items():
                if rel_type in types:
                    layer = layer_name
                    break

            # Add edge
            self.G.add_edge(
                source, target,
                relationship_type=rel_type,
                layer=layer,
                confidence=edge.get('confidence', 1.0),
                trial_id=edge.get('trial_id', ''),
                evidence_text=edge.get('evidence_text', ''),
                direction=edge.get('direction', 'directed'),
                temporal_marker=edge.get('temporal_marker'),
            )

            edge_counts[rel_type] += 1
            self.edge_count += 1

        print(f"  Added {self.G.number_of_edges()} edges")
        print("\n  Edges by type:")
        for rel_type, count in sorted(edge_counts.items()):
            print(f"    {rel_type}: {count}")

    def get_layer(self, layer_name: str) -> nx.DiGraph:
        """Extract a subgraph containing only edges from specified layer."""
        rel_types = self.LAYERS.get(layer_name, [layer_name])

        # Create subgraph with edges matching the layer
        subgraph = nx.DiGraph()

        for u, v, key, data in self.G.edges(data=True, keys=True):
            if data.get('relationship_type') in rel_types:
                if not subgraph.has_node(u):
                    subgraph.add_node(u, **self.G.nodes[u])
                if not subgraph.has_node(v):
                    subgraph.add_node(v, **self.G.nodes[v])
                subgraph.add_edge(u, v, **data)

        return subgraph

    def get_undirected_projection(self) -> nx.Graph:
        """Get undirected projection of the network."""
        return self.G.to_undirected()

    def get_simple_graph(self) -> nx.DiGraph:
        """Get simple directed graph (one edge per pair)."""
        simple = nx.DiGraph()

        # Add all nodes
        for node, attrs in self.G.nodes(data=True):
            simple.add_node(node, **attrs)

        # Add edges (keeping first occurrence of each pair)
        seen = set()
        for u, v, data in self.G.edges(data=True):
            if (u, v) not in seen:
                simple.add_edge(u, v, **data)
                seen.add((u, v))

        return simple

    def compute_basic_statistics(self) -> Dict:
        """Compute basic network statistics."""
        print("\n=== Computing Network Statistics ===")

        stats = {
            'num_nodes': self.G.number_of_nodes(),
            'num_edges': self.G.number_of_edges(),
        }

        # Undirected projection for connectivity
        G_undirected = self.G.to_undirected()

        # Components
        components = list(nx.connected_components(G_undirected))
        stats['num_components'] = len(components)
        stats['largest_component_size'] = len(max(components, key=len)) if components else 0
        stats['largest_component_fraction'] = stats['largest_component_size'] / stats['num_nodes']

        # Density
        stats['density'] = nx.density(G_undirected)

        # Degree statistics
        degrees = [d for n, d in G_undirected.degree()]
        stats['avg_degree'] = np.mean(degrees)
        stats['max_degree'] = max(degrees)
        stats['min_degree'] = min(degrees)

        # Node type distribution
        type_counts = defaultdict(int)
        for node, attrs in self.G.nodes(data=True):
            type_counts[attrs.get('entity_type', 'unknown')] += 1
        stats['node_types'] = dict(type_counts)

        # Gender distribution
        gender_counts = defaultdict(int)
        for node, attrs in self.G.nodes(data=True):
            gender_counts[attrs.get('gender', 'unknown')] += 1
        stats['genders'] = dict(gender_counts)

        # Edge type distribution
        edge_counts = defaultdict(int)
        for u, v, data in self.G.edges(data=True):
            edge_counts[data.get('relationship_type', 'unknown')] += 1
        stats['edge_types'] = dict(edge_counts)

        # Layer statistics
        layer_counts = defaultdict(int)
        for u, v, data in self.G.edges(data=True):
            layer_counts[data.get('layer', 'other')] += 1
        stats['layers'] = dict(layer_counts)

        print(f"\nNetwork Summary:")
        print(f"  Nodes: {stats['num_nodes']}")
        print(f"  Edges: {stats['num_edges']}")
        print(f"  Density: {stats['density']:.6f}")
        print(f"  Components: {stats['num_components']}")
        print(f"  Largest component: {stats['largest_component_size']} ({stats['largest_component_fraction']:.1%})")
        print(f"  Avg degree: {stats['avg_degree']:.2f}")

        return stats

    def export_graphml(self, filename: str = "full_network.graphml"):
        """Export graph to GraphML format."""
        print(f"\n=== Exporting to GraphML ===")

        # Convert to simple graph for export (GraphML doesn't support multigraph well)
        simple = self.get_simple_graph()

        # Clean attributes for GraphML compatibility
        for node in simple.nodes():
            for key, value in list(simple.nodes[node].items()):
                if isinstance(value, list):
                    simple.nodes[node][key] = str(value)
                elif value is None:
                    simple.nodes[node][key] = ''

        for u, v in simple.edges():
            for key, value in list(simple.edges[u, v].items()):
                if value is None:
                    simple.edges[u, v][key] = ''

        filepath = OUTPUT_DIR / filename
        nx.write_graphml(simple, filepath)
        print(f"  Saved {filepath}")

        return filepath

    def export_layers(self):
        """Export each layer as separate GraphML."""
        print("\n=== Exporting Layer Networks ===")

        for layer_name in self.LAYERS.keys():
            layer_graph = self.get_layer(layer_name)

            if layer_graph.number_of_edges() > 0:
                # Clean attributes
                for node in layer_graph.nodes():
                    for key, value in list(layer_graph.nodes[node].items()):
                        if isinstance(value, list):
                            layer_graph.nodes[node][key] = str(value)
                        elif value is None:
                            layer_graph.nodes[node][key] = ''

                for u, v in layer_graph.edges():
                    for key, value in list(layer_graph.edges[u, v].items()):
                        if value is None:
                            layer_graph.edges[u, v][key] = ''

                filepath = OUTPUT_DIR / f"{layer_name}_layer.graphml"
                nx.write_graphml(layer_graph, filepath)
                print(f"  Saved {layer_name}_layer.graphml ({layer_graph.number_of_edges()} edges)")

    def save_outputs(self, stats: Dict):
        """Save network and statistics."""
        print("\n=== Saving Outputs ===")

        # Export full network
        self.export_graphml("full_network.graphml")

        # Export layers
        self.export_layers()

        # Export undirected projection (simple graph)
        simple_undirected = nx.Graph()
        for node, attrs in self.G.nodes(data=True):
            clean_attrs = {}
            for k, v in attrs.items():
                if isinstance(v, list):
                    clean_attrs[k] = str(v)
                elif v is None:
                    clean_attrs[k] = ''
                else:
                    clean_attrs[k] = v
            simple_undirected.add_node(node, **clean_attrs)

        # Add edges (one per pair)
        seen_edges = set()
        for u, v, data in self.G.edges(data=True):
            edge_key = tuple(sorted([u, v]))
            if edge_key not in seen_edges:
                clean_data = {}
                for k, val in data.items():
                    if val is None:
                        clean_data[k] = ''
                    else:
                        clean_data[k] = val
                simple_undirected.add_edge(u, v, **clean_data)
                seen_edges.add(edge_key)

        nx.write_graphml(simple_undirected, OUTPUT_DIR / "undirected_network.graphml")
        print(f"  Saved undirected_network.graphml ({simple_undirected.number_of_edges()} edges)")

        # Save statistics
        with open(OUTPUT_DIR / "network_statistics.json", 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"  Saved network_statistics.json")

        # Save node list with attributes
        node_df = pd.DataFrame([
            {'name': name, **attrs}
            for name, attrs in self.G.nodes(data=True)
        ])
        node_df.to_csv(OUTPUT_DIR / "node_attributes.csv", index=False)
        print(f"  Saved node_attributes.csv ({len(node_df)} nodes)")

        # Save edge list
        edge_list = []
        for u, v, key, data in self.G.edges(data=True, keys=True):
            edge_list.append({
                'source': u,
                'target': v,
                'key': key,
                **data
            })
        edge_df = pd.DataFrame(edge_list)
        edge_df.to_csv(OUTPUT_DIR / "edge_list.csv", index=False)
        print(f"  Saved edge_list.csv ({len(edge_df)} edges)")

    def run(self):
        """Execute the full network construction pipeline."""
        print("=" * 70)
        print("NETWORK CONSTRUCTION PIPELINE")
        print("=" * 70)

        # Load data
        entities, edges = self.load_data()

        # Build node index
        nodes = self.build_node_index(entities, edges)

        # Construct graph
        self.add_nodes_to_graph(nodes)
        self.add_edges_to_graph(edges)

        # Compute statistics
        stats = self.compute_basic_statistics()

        # Save outputs
        self.save_outputs(stats)

        print("\n" + "=" * 70)
        print("CONSTRUCTION COMPLETE")
        print("=" * 70)
        print(f"\nNetwork created with {self.G.number_of_nodes()} nodes and {self.G.number_of_edges()} edges")
        print(f"Outputs saved to: {OUTPUT_DIR}")

        return self.G, stats


if __name__ == "__main__":
    network = WitchcraftNetwork()
    G, stats = network.run()
