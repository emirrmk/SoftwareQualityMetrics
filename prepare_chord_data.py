import json
from collections import defaultdict

def extract_hierarchy():
    with open('interaction_chain.json', 'r') as f:
        data = json.load(f)

    methods_by_service = defaultdict(set)
    links = []

    def process_call(source_service, source_method, call):
        target_service = call['service']
        target_method = call['method']
        
        methods_by_service[source_service].add(source_method)
        methods_by_service[target_service].add(target_method)
        
        links.append({
            "source": f"{source_service}.{source_method}",
            "target": f"{target_service}.{target_method}",
            "value": call.get('count', 1)
        })
        
        for sub_call in call.get('calls', []):
            process_call(target_service, target_method, sub_call)

    for item in data:
        service = item['service']
        method = item['method']
        methods_by_service[service].add(method)
        
        for call in item.get('calls', []):
            process_call(service, method, call)

    # Convert sets to sorted lists for stability
    nodes = []
    service_list = sorted(methods_by_service.keys())
    
    method_id_map = {}
    current_id = 0
    
    for service in service_list:
        sorted_methods = sorted(list(methods_by_service[service]))
        for method in sorted_methods:
            full_name = f"{service}.{method}"
            method_id_map[full_name] = current_id
            nodes.append({
                "id": current_id,
                "name": method,
                "service": service,
                "full_name": full_name
            })
            current_id += 1

    # Aggregate links with the same source and target
    aggregated_links = defaultdict(int)
    for link in links:
        key = (method_id_map[link['source']], method_id_map[link['target']])
        aggregated_links[key] += link['value']

    final_links = []
    for (src, tgt), val in aggregated_links.items():
        final_links.append({
            "source": src,
            "target": tgt,
            "value": val
        })

    output = {
        "nodes": nodes,
        "links": final_links,
        "services": service_list
    }

    with open('chord_data.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Extracted {len(nodes)} methods across {len(service_list)} services.")
    print(f"Created {len(final_links)} unique interactions.")

if __name__ == "__main__":
    extract_hierarchy()
