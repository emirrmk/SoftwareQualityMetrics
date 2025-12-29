import json
import os

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def extract_interactions_from_chain(chain_data):
    service_interactions = {} # (source, target) -> count
    api_interactions = set() # (source, source_method, target, endpoint, http_method)

    def process_calls(source_service, calls):
        for call in calls:
            target_service = call['service']
            endpoint = call['endpoint']
            http_method = call['http_method']
            count = call.get('count', 1)
            
            # Note: source_method is not directly available in the nested structure 
            # for the caller in interaction_chain.json, only for the root.
            # But we can still track service -> service
            key = (source_service, target_service)
            service_interactions[key] = service_interactions.get(key, 0) + count
            
            # Recurse
            process_calls(target_service, call.get('calls', []))

    for entry in chain_data:
        source_service = entry['service']
        source_method = entry['method']
        
        for call in entry['calls']:
            target_service = call['service']
            endpoint = call['endpoint']
            http_method = call['http_method']
            count = call.get('count', 1)
            
            key = (source_service, target_service)
            service_interactions[key] = service_interactions.get(key, 0) + count
            
            api_interactions.add((source_service, target_service, endpoint, http_method))
            
            # Recurse for deeper calls
            process_calls(target_service, call.get('calls', []))

    return service_interactions, api_interactions

def extract_interactions_from_results(results_data):
    service_interactions = {}
    for rel in results_data.get('relations', []):
        service_interactions[(rel['source'], rel['target'])] = rel['count']
    
    api_interactions = set()
    for api in results_data.get('api_interactions', []):
        api_interactions.add((api['source'], api['target'], api['endpoint'], api['http_method']))
        
    return service_interactions, api_interactions

def main():
    chain_file = '/Users/emirirmak/Desktop/SoftwareQualityMetricProject/interaction_chain.json'
    results_file = '/Users/emirirmak/Desktop/SoftwareQualityMetricProject/interactions_results.json'
    
    chain_data = load_json(chain_file)
    results_data = load_json(results_file)
    
    chain_service, chain_api = extract_interactions_from_chain(chain_data)
    results_service, results_api = extract_interactions_from_results(results_data)
    
    print("--- Service Interaction Comparison ---")
    all_keys = set(chain_service.keys()) | set(results_service.keys())
    inconsistent_service = False
    for key in sorted(all_keys):
        c_count = chain_service.get(key, 0)
        r_count = results_service.get(key, 0)
        if c_count != r_count:
            print(f"Mismatch for {key}: Chain={c_count}, Results={r_count}")
            inconsistent_service = True
    
    if not inconsistent_service:
        print("Service interactions are consistent.")
        
    print("\n--- API Interaction Comparison ---")
    missing_in_results = chain_api - results_api
    extra_in_results = results_api - chain_api
    
    if missing_in_results:
        print(f"Missing in results ({len(missing_in_results)}):")
        for item in sorted(missing_in_results):
            print(f"  {item}")
    else:
        print("No missing API interactions in results.")
        
    if extra_in_results:
        print(f"Extra in results ({len(extra_in_results)}):")
        for item in sorted(extra_in_results):
            print(f"  {item}")
    else:
        print("No extra API interactions in results.")

if __name__ == "__main__":
    main()
