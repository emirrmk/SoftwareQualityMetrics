import os
import re
import json
import collections

def get_interactions(root_dir, analyzed_services):
    interactions = []
    
    # Regex for getServiceUrl("service-name")
    service_url_regex = re.compile(r'(\w+)\s*=\s*getServiceUrl\("([^"]+)"\)')
    # Regex for restTemplate calls
    rest_template_regex = re.compile(r'restTemplate\.(exchange|getForObject|postForObject|put|delete)\(\s*([^,]+)(?:,\s*([^,]+))?')
    # Regex for method header to find source method
    method_header_regex = re.compile(r'(?:public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\) *(?:throws [^\{]+)?\{')
    package_regex = re.compile(r'package\s+([\w\.]+);')

    for service_path in analyzed_services:
        service_name = service_path.strip().replace("./", "")
        
        src_path = os.path.join(root_dir, service_name, "src", "main", "java")
        if not os.path.exists(src_path):
            continue
            
        for root, dirs, files in os.walk(src_path):
            for file in files:
                if file.endswith(".java") and "Test" not in file:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                        package_match = package_regex.search(content)
                        package_name = package_match.group(1) if package_match else ""
                        class_name = file.replace(".java", "")
                        full_class_name = f"{package_name}.{class_name}" if package_name else class_name

                        # Find all method headers and their start positions
                        methods = []
                        for m_match in method_header_regex.finditer(content):
                            methods.append({'name': m_match.group(1), 'start': m_match.start()})
                        
                        urls = {match.group(1): match.group(2) for match in service_url_regex.finditer(content)}
                        
                        for match in rest_template_regex.finditer(content):
                            call_pos = match.start()
                            template_method = match.group(1)
                            url_expr = match.group(2).strip()
                            arg2 = match.group(3).strip() if match.group(3) else ""
                            
                            # Find the source method (the one that contains this call)
                            source_method_name = "unknown"
                            for m in reversed(methods):
                                if m['start'] < call_pos:
                                    source_method_name = m['name']
                                    break
                            
                            source_method = f"{full_class_name}.{source_method_name}"

                            http_method = "GET"
                            if template_method == "postForObject": http_method = "POST"
                            elif template_method == "put": http_method = "PUT"
                            elif template_method == "delete": http_method = "DELETE"
                            elif template_method == "exchange":
                                if "HttpMethod." in arg2:
                                    http_method = arg2.split(".")[-1]
                            
                            target_service = "unknown"
                            endpoint = "unknown"
                            
                            for var, svc in urls.items():
                                if url_expr.startswith(var):
                                    target_service = svc
                                    path_match = re.search(r'"([^"]+)"', url_expr)
                                    if path_match:
                                        endpoint = path_match.group(1)
                                    break
                            
                            if target_service == "unknown":
                                svc_direct_match = re.search(r'getServiceUrl\("([^"]+)"\)', url_expr)
                                if svc_direct_match:
                                    target_service = svc_direct_match.group(1)
                                    path_match = re.search(r'\+\s*"([^"]+)"', url_expr)
                                    if path_match:
                                        endpoint = path_match.group(1)
                            
                            if target_service != "unknown":
                                interactions.append({
                                    'source': service_name,
                                    'source_method': source_method,
                                    'target': target_service,
                                    'endpoint': endpoint,
                                    'http_method': http_method
                                })
                                
    return interactions

def main():
    root_dir = '/Users/emirirmak/Desktop/SoftwareQualityMetricProject'
    analyzed_services_file = os.path.join(root_dir, 'analyzed_services.txt')
    
    if not os.path.exists(analyzed_services_file):
        return

    with open(analyzed_services_file, 'r') as f:
        services = [line.strip() for line in f if line.strip()]

    results = get_interactions(root_dir, services)

    api_interactions = []
    relation_counts = {}

    for item in results:
        key = (item['source'], item['target'])
        relation_counts[key] = relation_counts.get(key, 0) + 1
        api_interactions.append(item)

    output = {
        'total_relations': len(relation_counts),
        'relations': [
            {'source': src, 'target': tgt, 'count': count}
            for (src, tgt), count in relation_counts.items()
        ],
        'api_interactions': api_interactions
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
