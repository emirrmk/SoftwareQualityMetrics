import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os
import json

# Paths
CK_OUTPUT_DIR = "ck_output"
OUTPUT_DIR = "pca_results"
CLASS_CSV = os.path.join(CK_OUTPUT_DIR, "class.csv")
METHOD_CSV = os.path.join(CK_OUTPUT_DIR, "method.csv")

# Microservices list (same as restructure_metrics.py)
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

def get_ms_name(file_path):
    for s in SERVICES:
        if f"/{s}/" in file_path:
            return s
    return None

def is_business_logic(row):
    path = row['file'].lower()
    name = row['class'].lower()
    if "/src/test/" in path or "old-docs" in path:
        return False
    if "controller" in path or "controller" in name or "service" in path or "service" in name:
        return True
    return False

# Features
CLASS_FEATURES = [
    'cbo', 'cboModified', 'fanin', 'fanout', 'wmc', 'dit', 'noc', 'rfc', 'lcom', 'lcom*', 
    'tcc', 'lcc', 'totalMethodsQty', 'staticMethodsQty', 'publicMethodsQty', 'privateMethodsQty', 
    'protectedMethodsQty', 'defaultMethodsQty', 'visibleMethodsQty', 'abstractMethodsQty', 
    'finalMethodsQty', 'synchronizedMethodsQty', 'totalFieldsQty', 'staticFieldsQty', 
    'publicFieldsQty', 'privateFieldsQty', 'protectedFieldsQty', 'defaultFieldsQty', 
    'finalFieldsQty', 'synchronizedFieldsQty', 'nosi', 'loc', 'returnQty', 'loopQty', 
    'comparisonsQty', 'tryCatchQty', 'parenthesizedExpsQty', 'stringLiteralsQty', 
    'numbersQty', 'assignmentsQty', 'mathOperationsQty', 'variablesQty', 
    'maxNestedBlocksQty', 'anonymousClassesQty', 'innerClassesQty', 'lambdasQty', 
    'uniqueWordsQty', 'logStatementsQty'
]

METHOD_FEATURES = [
    'cbo', 'cboModified', 'fanin', 'fanout', 'wmc', 'rfc', 'loc', 'returnsQty', 
    'variablesQty', 'parametersQty', 'methodsInvokedQty', 'methodsInvokedLocalQty', 
    'methodsInvokedIndirectLocalQty', 'loopQty', 'comparisonsQty', 'tryCatchQty', 
    'parenthesizedExpsQty', 'stringLiteralsQty', 'numbersQty', 'assignmentsQty', 
    'mathOperationsQty', 'maxNestedBlocksQty', 'anonymousClassesQty', 'innerClassesQty', 
    'lambdasQty', 'uniqueWordsQty', 'logStatementsQty'
]

def run_pca(df, features, prefix):
    if len(df) < 2:
        return None
    
    X = df[features].apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # PCA
    pca = PCA()
    pca.fit(X_scaled)
    
    # Variance
    variance_ratio = pca.explained_variance_ratio_.tolist()
    
    # Loadings (how each feature contributes to each component)
    loadings = pd.DataFrame(pca.components_.T, columns=[f'PC{i+1}' for i in range(pca.n_components_)], index=features)
    
    return {
        "variance_ratio": variance_ratio,
        "loadings": loadings.to_dict()
    }

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # Load data
    print("Loading data...")
    df_class = pd.read_csv(CLASS_CSV)
    df_method = pd.read_csv(METHOD_CSV)
    
    # Filter Business Logic
    print("Filtering business logic...")
    df_class_bl = df_class[df_class.apply(is_business_logic, axis=1)].copy()
    df_method_bl = df_method[df_method.apply(is_business_logic, axis=1)].copy()
    
    # Add MS column
    df_class_bl['ms'] = df_class_bl['file'].apply(get_ms_name)
    df_method_bl['ms'] = df_method_bl['file'].apply(get_ms_name)
    
    results = {
        "project_level": {},
        "microservice_level": {}
    }
    
    # 1. Project Level
    print("Executing Project-Level PCA...")
    results["project_level"]["class"] = run_pca(df_class_bl, CLASS_FEATURES, "project_class")
    results["project_level"]["method"] = run_pca(df_method_bl, METHOD_FEATURES, "project_method")
    
    # 2. MS Level
    print("Executing Microservice-Level PCA...")
    for ms in SERVICES:
        ms_class = df_class_bl[df_class_bl['ms'] == ms]
        ms_method = df_method_bl[df_method_bl['ms'] == ms]
        
        ms_results = {}
        if len(ms_class) >= 5: # Need enough samples for meaningful PCA
            ms_results["class"] = run_pca(ms_class, CLASS_FEATURES, f"{ms}_class")
        
        if len(ms_method) >= 5:
            ms_results["method"] = run_pca(ms_method, METHOD_FEATURES, f"{ms}_method")
            
        if ms_results:
            results["microservice_level"][ms] = ms_results
            
    # Save
    with open(os.path.join(OUTPUT_DIR, "pca_results.json"), 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"PCA complete. Results saved to {OUTPUT_DIR}/pca_results.json")

if __name__ == "__main__":
    main()
