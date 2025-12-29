import json
import collections
import os

def generate_mermaid():
    root_dir = '/Users/emirirmak/Desktop/SoftwareQualityMetricProject'
    chain_file = os.path.join(root_dir, 'interaction_chain.json')
    
    if not os.path.exists(chain_file):
        print("Error: interaction_chain.json not found")
        return

    with open(chain_file, 'r') as f:
        chains = json.load(f)

    # Dictionary to store Service A -> Service B -> Weight
    service_edges = collections.defaultdict(lambda: collections.defaultdict(int))

    def extract_edges(node, source_svc):
        if 'calls' in node:
            for call in node['calls']:
                target_svc = call['service']
                weight = call.get('count', 1)
                service_edges[source_svc][target_svc] += weight
                extract_edges(call, target_svc)

    for top_node in chains:
        extract_edges(top_node, top_node['service'])

    # Format into Mermaid
    mermaid = ["graph LR"]
    # We want to represent weights by line thickness or just labels.
    # Mermaid doesn't strictly have "thickness" for weights but we can use labels.
    for src, targets in service_edges.items():
        for tgt, weight in targets.items():
            # src -->|weight| tgt
            mermaid.append(f"    {src} -- \"{weight}\" --> {tgt}")

    print("\n".join(mermaid))

if __name__ == "__main__":
    generate_mermaid()
