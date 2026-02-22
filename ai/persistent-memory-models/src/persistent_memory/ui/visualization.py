"""Visualization utilities for knowledge graph and metrics."""

import json

import matplotlib.pyplot as plt
import networkx as nx


def visualize_knowledge_graph(kg_path: str, output_path: str = "graph.png"):
    """Visualize the knowledge graph."""
    # Load graph
    with open(kg_path) as f:
        data = json.load(f)

    g = nx.node_link_graph(data)

    # Create visualization
    plt.figure(figsize=(20, 20))
    pos = nx.spring_layout(g, k=0.5, iterations=50)

    # Draw nodes
    nx.draw_networkx_nodes(g, pos, node_color="lightblue", node_size=500, alpha=0.9)

    # Draw edges
    nx.draw_networkx_edges(g, pos, edge_color="gray", arrows=True, arrowsize=20, alpha=0.5)

    # Draw labels
    nx.draw_networkx_labels(g, pos, font_size=8, font_family="sans-serif")

    # Draw edge labels
    edge_labels = nx.get_edge_attributes(g, "predicate")
    nx.draw_networkx_edge_labels(g, pos, edge_labels, font_size=6)

    plt.title("Knowledge Graph Visualization", fontsize=16)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Graph saved to {output_path}")


def plot_metrics_timeline(metrics: dict[str, list[float]], output_path: str = "metrics.png"):
    """Plot metrics over time."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Query latency
    axes[0, 0].plot(metrics.get("query_latency", []))
    axes[0, 0].set_title("Query Latency")
    axes[0, 0].set_ylabel("ms")
    axes[0, 0].grid(True)

    # Precision/Recall
    axes[0, 1].plot(metrics.get("precision", []), label="Precision")
    axes[0, 1].plot(metrics.get("recall", []), label="Recall")
    axes[0, 1].set_title("Retrieval Quality")
    axes[0, 1].legend()
    axes[0, 1].grid(True)

    # Vector store size
    axes[1, 0].plot(metrics.get("vector_store_size", []))
    axes[1, 0].set_title("Vector Store Size")
    axes[1, 0].set_ylabel("# items")
    axes[1, 0].grid(True)

    # Graph size
    axes[1, 1].plot(metrics.get("graph_nodes", []), label="Nodes")
    axes[1, 1].plot(metrics.get("graph_edges", []), label="Edges")
    axes[1, 1].set_title("Knowledge Graph Size")
    axes[1, 1].legend()
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Metrics plot saved to {output_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        visualize_knowledge_graph(sys.argv[1])
