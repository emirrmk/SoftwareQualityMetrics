import json
import os
from pathlib import Path

def filter_metrics(obj):
    """
    Recursively filter out default values (0, 0.0, '0', '0.0', 'false', False) 
    from dictionaries named 'metrics'.
    """
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if k == "metrics" and isinstance(v, dict):
                # Filter this metrics dictionary
                filtered_v = {}
                for mk, mv in v.items():
                    # Default values to filter out
                    if mv in [0, 0.0, "0", "0.0", "false", False]:
                        continue
                    filtered_v[mk] = mv
                new_dict[k] = filtered_v
            else:
                # Recursively process
                new_dict[k] = filter_metrics(v)
        return new_dict
    elif isinstance(obj, list):
        return [filter_metrics(i) for i in obj]
    else:
        return obj

def main():
    input_dir = Path("/Users/emirirmak/Desktop/SoftwareQualityMetricProject/metrics")
    output_dir = Path("/Users/emirirmak/Desktop/SoftwareQualityMetricProject/filtered_metrics")
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        print(f"Created directory: {output_dir}")

    for json_file in input_dir.glob("*.json"):
        print(f"Processing {json_file.name}...")
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            filtered_data = filter_metrics(data)
            
            output_file = output_dir / json_file.name
            with open(output_file, 'w') as f:
                json.dump(filtered_data, f, indent=2)
                
        except Exception as e:
            print(f"Error processing {json_file}: {e}")

if __name__ == "__main__":
    main()
