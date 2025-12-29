import os
import re
import json
import collections

def parse_controllers(root_dir):
    service_mappings = collections.defaultdict(list)
    
    class_mapping_regex = re.compile(r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?["\']?([^"\'\)]+)["\']?(?:,\s*method\s*=\s*RequestMethod\.(\w+))?')
    method_mapping_regex = re.compile(r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*(?:(?:value|path)\s*=\s*)?["\']?([^"\'\),]+)?["\']?(?:,\s*method\s*=\s*RequestMethod\.(\w+))?')
    method_header_regex = re.compile(r'public\s+\S+\s+(\w+)\s*\(([^)]*)\)')
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

def augment_metrics():
    root_dir = '/Users/emirirmak/Desktop/SoftwareQualityMetricProject'
    interactions_file = os.path.join(root_dir, 'interactions_results.json')
    metrics_dir = os.path.join(root_dir, 'filtered_metrics')
    
    if not os.path.exists(interactions_file): return

    with open(interactions_file, 'r') as f:
        interactions_data = json.load(f)
        api_interactions = interactions_data.get('api_interactions', [])

    service_mappings = parse_controllers(root_dir)
    invocations = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(int))))
    
    for inter in api_interactions:
        match = match_interaction(inter, service_mappings)
        if match:
            invocations[inter['target']][match['class']][match['method_name']][inter['source']] += 1

    for filename in os.listdir(metrics_dir):
        if not filename.endswith(".json"): continue
        service_name = filename.replace(".json", "")
        file_path = os.path.join(metrics_dir, filename)
        
        with open(file_path, 'r') as f:
            metrics_data = json.load(f)

        service_total = 0
        for class_name, class_data in metrics_data.get('classes', {}).items():
            class_total = 0
            if 'metrics' not in class_data: class_data['metrics'] = {}
            
            # Clean up old class-level fields
            if 'total_invocation_point_number' in class_data['metrics']:
                del class_data['metrics']['total_invocation_point_number']
            
            for method_sig, method_data in class_data.get('methods', {}).items():
                method_name = method_sig.split('/')[0]
                method_invs = invocations.get(service_name, {}).get(class_name, {}).get(method_name, {})
                
                # Clean up old method-level fields
                if 'invocations' in method_data: del method_data['invocations']
                if 'total_invocation_point_number' in method_data['metrics']:
                    del method_data['metrics']['total_invocation_point_number']
                
                # ALWAYS remove "line" field
                if 'line' in method_data['metrics']:
                    del method_data['metrics']['line']
                
                if method_invs:
                    method_data['invocations'] = method_invs
                    total = sum(method_invs.values())
                    method_data['metrics']['external_microservice_call'] = total
                    class_total += total
                # If total_invocation_point_number was 0, we don't add the new field
            
            if class_total > 0:
                class_data['metrics']['external_microservice_call'] = class_total
            
            service_total += class_total
        
        # Clean up old service-level fields
        if 'total_invocation_point_number' in metrics_data:
            del metrics_data['total_invocation_point_number']
            
        if service_total > 0:
            metrics_data['external_microservice_call'] = service_total
        
        with open(file_path, 'w') as f:
            json.dump(metrics_data, f, indent=2)
            
    print(f"Refined and Augmented {len(os.listdir(metrics_dir))} metric files.")

if __name__ == "__main__":
    augment_metrics()
