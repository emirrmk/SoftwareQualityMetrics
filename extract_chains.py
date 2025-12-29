import os
import re
import json
import collections

def parse_controllers(root_dir):
    service_mappings = collections.defaultdict(list)
    
    class_mapping_regex = re.compile(r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?["\']?([^"\'\)]+)["\']?(?:,\s*method\s*=\s*RequestMethod\.(\w+))?')
    method_mapping_regex = re.compile(r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*(?:(?:value|path)\s*=\s*)?["\']?([^"\'\),]+)?["\']?(?:,\s*method\s*=\s*RequestMethod\.(\w+))?')
    method_header_regex = re.compile(r'(?:public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\) *(?:throws [^\{]+)?\{')
    package_regex = re.compile(r'package\s+([\w\.]+);')

    for root, dirs, files in os.walk(root_dir):
        if "src/main/java" not in root:
            continue
            
        service_name = None
        parts = root.split(os.sep)
        for i, part in enumerate(parts):
            if part.startswith("ts-") and part.endswith("-service"):
                service_name = part
                break
        
        if not service_name: continue

        for file in files:
            if file.endswith("Controller.java"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    package_match = package_regex.search(content)
                    package_full_name = package_match.group(1) if package_match else ""
                    class_full_name = package_full_name + "." + file.replace(".java", "")
                    
                    class_mapping_match = class_mapping_regex.search(content)
                    base_path = class_mapping_match.group(1).strip("/") if class_mapping_match else ""
                    
                    for match in method_mapping_regex.finditer(content):
                        mapping_type = match.group(1)
                        path_in_method = match.group(2).strip("/") if match.group(2) else ""
                        full_path = "/".join(filter(None, [base_path, path_in_method]))
                        
                        http_method = "GET"
                        if mapping_type == "Post": http_method = "POST"
                        elif mapping_type == "Put": http_method = "PUT"
                        elif mapping_type == "Delete": http_method = "DELETE"
                        elif mapping_type == "Patch": http_method = "PATCH"
                        elif mapping_type == "Request" and match.group(3):
                            http_method = match.group(3).upper()
                        
                        header_match = method_header_regex.search(content, match.end())
                        if header_match:
                            method_name = header_match.group(1)
                            service_mappings[service_name].append({
                                'class': class_full_name,
                                'method_name': method_name,
                                'path': full_path,
                                'http_method': http_method,
                                'regex': re.compile("^/?" + re.sub(r'\{[^}]+\}', r'[^/]+', full_path) + "/?$")
                            })
                            
    return service_mappings

def match_interaction(interaction, service_mappings):
    target_service = interaction['target']
    raw_endpoint = interaction['endpoint'].strip('"')
    endpoint = raw_endpoint.strip("/")
    http_method = interaction.get('http_method', 'GET').upper()
    
    if target_service not in service_mappings:
        return None
        
    for mapping in service_mappings[target_service]:
        if mapping['http_method'] != http_method: continue
        
        mapping_path = mapping['path'].strip("/")
        
        if mapping['regex'].match(raw_endpoint if raw_endpoint.startswith("/") else "/" + raw_endpoint):
            return mapping
            
        if endpoint == mapping_path:
            return mapping
            
        if raw_endpoint.endswith("/") and mapping_path.startswith(endpoint) and "{" in mapping['path']:
            return mapping
            
    return None

def build_internal_call_graph(root_dir):
    internal_calls = collections.defaultdict(lambda: collections.defaultdict(set))
    all_methods = collections.defaultdict(set)
    method_header_regex = re.compile(r'(?:public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\) *(?:throws [^\{]+)?\{')

    for root, dirs, files in os.walk(root_dir):
        if "src/main/java" not in root: continue
        
        service_name = None
        for part in root.split(os.sep):
            if part.startswith("ts-") and part.endswith("-service"):
                service_name = part
                break
        if not service_name: continue

        for file in files:
            if file.endswith(".java"):
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                    
                    matches = list(method_header_regex.finditer(content))
                    for i, m in enumerate(matches):
                        name = m.group(1)
                        all_methods[service_name].add(name)
                        
                        start = m.end()
                        end = matches[i+1].start() if i+1 < len(matches) else len(content)
                        body = content[start:end]
                        
                        calls = re.findall(r'(\w+)\(', body)
                        for c in calls:
                            internal_calls[service_name][name].add(c)
                             
    return internal_calls, all_methods

def build_chains():
    root_dir = '/Users/emirirmak/Desktop/SoftwareQualityMetricProject'
    interactions_file = os.path.join(root_dir, 'interactions_results.json')
    
    if not os.path.exists(interactions_file): return

    with open(interactions_file, 'r') as f:
        interactions_data = json.load(f)
        api_interactions = interactions_data.get('api_interactions', [])

    service_mappings = parse_controllers(root_dir)
    internal_graph, all_methods = build_internal_call_graph(root_dir)
    
    reachable = collections.defaultdict(lambda: collections.defaultdict(set))
    for svc, calls in internal_graph.items():
        for start_method in all_methods[svc]:
            stack = [start_method]
            visited = set()
            while stack:
                curr = stack.pop()
                if curr not in visited:
                    visited.add(curr)
                    for neighbor in internal_graph[svc].get(curr, []):
                        if neighbor in all_methods[svc]:
                            stack.append(neighbor)
            reachable[svc][start_method] = visited

    source_interactions = collections.defaultdict(lambda: collections.defaultdict(list))
    for inter in api_interactions:
        method_name = inter['source_method'].split('.')[-1]
        source_interactions[inter['source']][method_name].append(inter)

    def get_calls_for_method(svc, method_name):
        results = []
        possible_methods = reachable[svc].get(method_name, {method_name})
        for m in possible_methods:
            if m in source_interactions.get(svc, {}):
                results.extend(source_interactions[svc][m])
        return results

    def trace(svc, method_name, visited=None):
        if visited is None: visited = set()
        node_id = f"{svc}:{method_name}"
        if node_id in visited: return {"service": svc, "method": method_name, "loop": True}
        
        node = {
            "service": svc,
            "method": method_name,
            "calls": []
        }
        
        outgoing = get_calls_for_method(svc, method_name)
        
        # Aggregate identical outgoing calls from this node
        # Group by target, endpoint, http_method
        grouped_calls = collections.defaultdict(int)
        call_details = {} # Map (t, e, h) -> interaction_obj
        
        for inter in outgoing:
            match = match_interaction(inter, service_mappings)
            if not match: continue
            
            key = (inter['target'], inter['endpoint'], inter['http_method'], match['method_name'])
            grouped_calls[key] += 1
            call_details[key] = (inter, match)

        for key, count in grouped_calls.items():
            inter, match = call_details[key]
            child = trace(inter['target'], match['method_name'], visited | {node_id})
            child['endpoint'] = inter['endpoint']
            child['http_method'] = inter['http_method']
            child['count'] = count
            node['calls'].append(child)
            
        return node

    is_target = collections.defaultdict(set)
    for inter in api_interactions:
        match = match_interaction(inter, service_mappings)
        if match:
            is_target[inter['target']].add(match['method_name'])
            
    final_chains = []
    seen_top_level = {} # Map canonical string -> node

    for svc in list(source_interactions.keys()):
        for m_name in list(source_interactions[svc].keys()):
            if m_name not in is_target[svc]:
                chain = trace(svc, m_name)
                if chain['calls']:
                    # Canonicalize for top-level merge
                    canon = json.dumps(chain, sort_keys=True)
                    if canon in seen_top_level:
                        seen_top_level[canon]['count'] = seen_top_level[canon].get('count', 1) + 1
                    else:
                        seen_top_level[canon] = chain
                        final_chains.append(chain)

    with open(os.path.join(root_dir, 'interaction_chain.json'), 'w') as f:
        json.dump(final_chains, f, indent=2)

    print(f"Generated and aggregated interaction chains.")

if __name__ == "__main__":
    build_chains()
