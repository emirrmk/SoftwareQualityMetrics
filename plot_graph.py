import json
import collections
import os
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np

FIB = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]

def get_fib_rank(val):
    for i, f in enumerate(FIB):
        if val <= f:
            return i
    return len(FIB) - 1

def load_all_services(root_dir):
    service_file = os.path.join(root_dir, 'analyzed_services.txt')
    services = []
    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            for line in f:
                name = line.strip().replace("./", "")
                if name:
                    services.append(name)
    return services

def get_interactions(chains):
    edges = collections.defaultdict(int)
    def extract_edges(node, source_svc):
        if 'calls' in node:
            for call in node['calls']:
                target_svc = call['service']
                weight = call.get('count', 1)
                edges[(source_svc, target_svc)] += weight
                extract_edges(call, target_svc)
    for top_node in chains:
        extract_edges(top_node, top_node['service'])
    return edges

def plot_single_graph(G, all_services, node_weights, title, output_path, mode="fan-in"):
    plt.figure(figsize=(32, 24))
    
    # Separate connected and isolated nodes
    connected_nodes = [n for n in all_services if G.degree(n) > 0]
    isolated_nodes = [n for n in all_services if G.degree(n) == 0]
    
    # Layout for connected nodes
    pos = nx.spring_layout(G.subgraph(connected_nodes), k=4.0, iterations=150, seed=42)
    
    # Position isolated nodes in a grid in the top-left
    grid_cols = 5
    for i, node in enumerate(isolated_nodes):
        row = i // grid_cols
        col = i % grid_cols
        # Use coordinates outside the spring layout range (usually [-1,1])
        pos[node] = np.array([-3.5 + col*0.4, 3.5 - row*0.4])

    # Node styling
    node_ranks = [get_fib_rank(node_weights[node]) for node in all_services]
    node_sizes = [1500 + 1200 * r for r in node_ranks]
    
    edge_weights = [d['weight'] for u, v, d in G.edges(data=True)]
    edge_ranks = [get_fib_rank(w) for w in edge_weights]
    
    # High contrast discrete colormap (Avoiding yellows)
    base_cmap = plt.get_cmap('tab20')
    colors_filtered = [base_cmap(i) for i in range(20) if i not in [15, 17, 19]]
    
    def get_color(rank):
        return colors_filtered[rank % len(colors_filtered)]

    edge_colors = [get_color(r) for r in edge_ranks]
    max_w = max(edge_weights) if edge_weights else 1
    edge_widths = [1 + 7 * (w / max_w) for w in edge_weights]

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, nodelist=all_services, node_size=node_sizes, 
                           node_color='lightgray', alpha=0.9, edgecolors='black')
    
    # Draw edges
    nx.draw_networkx_edges(
        G, pos, 
        width=edge_widths, 
        edge_color=edge_colors,
        arrowsize=40, 
        alpha=0.8, 
        connectionstyle='arc3,rad=0.2',
        min_source_margin=30,
        min_target_margin=30
    )
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif', font_weight='bold')
    
    # Edge weight labels
    edge_labels = { (u, v): d['weight'] for u, v, d in G.edges(data=True) }
    nx.draw_networkx_edge_labels(
        G, pos, 
        edge_labels=edge_labels, 
        font_size=9,
        label_pos=0.4,
        rotate=False,
        bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', boxstyle='round')
    )

    # Legends
    unique_ranks = sorted(list(set(edge_ranks)))
    edge_legend_elements = []
    for r in unique_ranks:
        color = get_color(r)
        edge_legend_elements.append(mlines.Line2D([], [], color=color, marker='_', linestyle='None',
                                              markersize=15, markeredgewidth=4, label=f"Weight <= {FIB[r]}"))
    
    if edge_legend_elements:
        edge_legend = plt.legend(handles=edge_legend_elements, title="Edge Weights (Fibonacci)", 
                                 loc="lower right", fontsize=12, title_fontsize=14, frameon=True, shadow=True)
        plt.gca().add_artist(edge_legend)

    unique_node_ranks = sorted(list(set(node_ranks)))
    if len(unique_node_ranks) > 6:
        sample_ranks = [unique_node_ranks[0], unique_node_ranks[len(unique_node_ranks)//2], unique_node_ranks[-1]]
    else:
        sample_ranks = unique_node_ranks
        
    node_legend_elements = []
    for r in sample_ranks:
        node_legend_elements.append(mlines.Line2D([], [], color='lightgray', marker='o', linestyle='None',
                                              markersize=10 + r*2, markeredgecolor='black', label=f"{mode.capitalize()} <= {FIB[r]}"))
    
    plt.legend(handles=node_legend_elements, title=f"Node {mode.capitalize()} (Size)", 
               loc="lower left", fontsize=12, title_fontsize=14, frameon=True, shadow=True)

    plt.title(title, fontsize=32, pad=50)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    root_dir = '/Users/emirirmak/Desktop/SoftwareQualityMetricProject'
    chain_file = os.path.join(root_dir, 'interaction_chain.json')
    all_services = load_all_services(root_dir)
    
    if not os.path.exists(chain_file):
        print("Error: interaction_chain.json not found")
        return

    with open(chain_file, 'r') as f:
        chains = json.load(f)

    edges = get_interactions(chains)
    
    # 1. Fan-In Graph
    G_in = nx.DiGraph()
    G_in.add_nodes_from(all_services)
    in_weights = {s: 0 for s in all_services}
    for (src, tgt), w in edges.items():
        G_in.add_edge(src, tgt, weight=w)
        in_weights[tgt] += w
    
    plot_single_graph(G_in, all_services, in_weights, 
                     "Microservice Interaction - Fan-In Visualization", 
                     os.path.join(root_dir, 'fan_in_graph.png'), mode="Fan-In")

    # 2. Fan-Out Graph
    G_out = nx.DiGraph()
    G_out.add_nodes_from(all_services)
    out_weights = {s: 0 for s in all_services}
    for (src, tgt), w in edges.items():
        G_out.add_edge(src, tgt, weight=w)
        out_weights[src] += w
        
    plot_single_graph(G_out, all_services, out_weights, 
                     "Microservice Interaction - Fan-Out Visualization", 
                     os.path.join(root_dir, 'fan_out_graph.png'), mode="Fan-Out")

    print(f"Generated Fan-In and Fan-Out graphs for {len(all_services)} services.")

if __name__ == "__main__":
    main()
