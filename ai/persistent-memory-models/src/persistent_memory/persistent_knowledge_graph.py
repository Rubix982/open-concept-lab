import networkx as nx
import json
import os
from typing import List, Dict, Any

class PersistentKnowledgeGraph:
    """
    Wrapper around NetworkX for knowledge graph storage.
    For MVP, this persists to a JSON file. Future versions will use Neo4j.
    """
    
    def __init__(self, persistence_path: str = "knowledge_graph.json"):
        self.persistence_path = persistence_path
        self.graph = nx.MultiDiGraph()
        self._load()

    def add_fact(self, subject: str, predicate: str, object: str, metadata: Dict[str, Any] = None):
        """
        Add a fact (edge) to the graph.
        """
        self.graph.add_node(subject, type="entity")
        self.graph.add_node(object, type="entity")
        self.graph.add_edge(subject, object, relation=predicate, **(metadata or {}))
        self._save()

    def get_subgraph(self, entity: str, depth: int = 1) -> Dict[str, Any]:
        """
        Retrieve the subgraph surrounding an entity.
        """
        if entity not in self.graph:
            return {"nodes": [], "edges": []}
            
        subgraph = nx.ego_graph(self.graph, entity, radius=depth)
        return nx.node_link_data(subgraph)

    def _save(self):
        """Save graph to disk."""
        data = nx.node_link_data(self.graph)
        with open(self.persistence_path, 'w') as f:
            json.dump(data, f)

    def _load(self):
        """Load graph from disk if exists."""
        if os.path.exists(self.persistence_path):
            with open(self.persistence_path, 'r') as f:
                data = json.load(f)
                self.graph = nx.node_link_graph(data)