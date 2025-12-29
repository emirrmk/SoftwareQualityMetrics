import csv
import json
import os
from collections import defaultdict

# Configuration
CK_OUTPUT_DIR = "/Users/emirirmak/Desktop/SoftwareQualityMetricProject/ck_output"
OUTPUT_DIR = "/Users/emirirmak/Desktop/SoftwareQualityMetricProject/metrics"
ROOT_DIR = "/Users/emirirmak/Desktop/SoftwareQualityMetricProject"

# Pre-identify microservices from the directory structure
SERVICES = [
    "ts-admin-basic-info-service", "ts-admin-order-service", "ts-admin-route-service",
    "ts-admin-travel-service", "ts-admin-user-service", "ts-assurance-service",
    "ts-auth-service", "ts-basic-service", "ts-cancel-service", "ts-common",
    "ts-config-service", "ts-consign-price-service", "ts-consign-service",
    "ts-contacts-service", "ts-delivery-service", "ts-execute-service",
    "ts-food-delivery-service", "ts-food-service", "ts-gateway-service",
    "ts-inside-payment-service", "ts-notification-service", "ts-order-other-service",
    "ts-order-service", "ts-payment-service", "ts-preserve-other-service",
    "ts-preserve-service", "ts-price-service", "ts-rebook-service",
    "ts-route-plan-service", "ts-route-service", "ts-seat-service",
    "ts-security-service", "ts-station-food-service", "ts-station-service",
    "ts-train-food-service", "ts-train-service", "ts-travel-plan-service",
    "ts-travel-service", "ts-travel2-service", "ts-user-service",
    "ts-verification-code-service", "ts-wait-order-service"
]

def get_microservice_name(file_path):
    # Normalize path and check if it belongs to a known microservice
    for service in SERVICES:
        if f"/{service}/" in file_path:
            return service
    return None

def categorize(path, classname):
    path = path.lower()
    classname = classname.lower()
    
    # Exclude tests and docs
    if "/src/test/" in path or "old-docs" in path:
        return "Exclude"
    
    # Business Logic
    if "controller" in path or "controller" in classname:
        return "Business Logic"
    if "service" in path or "service" in classname:
        return "Business Logic"
    
    # Everything else is boilerplate or infra
    return "Exclude"

def restructure():
    # Structure: data[microservice][class][method]
    data = defaultdict(lambda: {"classes": defaultdict(lambda: {"metrics": {}, "methods": defaultdict(lambda: {"metrics": {}, "field_usages": {}, "variable_usages": {}})})})

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Process class.csv
    print("Processing class.csv...")
    with open(os.path.join(CK_OUTPUT_DIR, "class.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if categorize(row['file'], row['class']) != "Business Logic":
                continue
                
            ms = get_microservice_name(row['file'])
            if not ms:
                continue
            
            classname = row['class']
            metrics = {k: v for k, v in row.items() if k not in ['file', 'class', 'type']}
            data[ms]["classes"][classname]["metrics"] = metrics

    # 2. Process method.csv
    print("Processing method.csv...")
    with open(os.path.join(CK_OUTPUT_DIR, "method.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if categorize(row['file'], row['class']) != "Business Logic":
                continue
                
            ms = get_microservice_name(row['file'])
            if not ms:
                continue
            
            classname = row['class']
            methodname = row['method']
            metrics = {k: v for k, v in row.items() if k not in ['file', 'class', 'method', 'type']}
            data[ms]["classes"][classname]["methods"][methodname]["metrics"] = metrics

    # 3. Process variable.csv
    print("Processing variable.csv...")
    with open(os.path.join(CK_OUTPUT_DIR, "variable.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if categorize(row['file'], row['class']) != "Business Logic":
                continue
                
            ms = get_microservice_name(row['file'])
            if not ms:
                continue
            
            classname = row['class']
            methodname = row['method']
            varname = row['variable']
            usage = row['usage']
            data[ms]["classes"][classname]["methods"][methodname]["variable_usages"][varname] = usage

    # 4. Process field.csv
    print("Processing field.csv...")
    with open(os.path.join(CK_OUTPUT_DIR, "field.csv"), mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if categorize(row['file'], row['class']) != "Business Logic":
                continue
                
            ms = get_microservice_name(row['file'])
            if not ms:
                continue
            
            classname = row['class']
            methodname = row['method']
            fieldname = row['variable'] 
            usage = row['usage']
            data[ms]["classes"][classname]["methods"][methodname]["field_usages"][fieldname] = usage

    # Write per-microservice JSON files
    print("Writing JSON files...")
    for ms, ms_data in data.items():
        ms_data["microservice_name"] = ms
        output_file = os.path.join(OUTPUT_DIR, f"{ms}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ms_data, f, indent=2)
    
    print(f"Done! JSON files generated in {OUTPUT_DIR}")

if __name__ == "__main__":
    restructure()
