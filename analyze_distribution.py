import csv
from collections import defaultdict

CK_CLASS_CSV = "ck_output/class.csv"

def categorize(path, classname):
    path = path.lower()
    classname = classname.lower()
    
    if "/src/test/" in path:
        return "Test"
    
    if "controller" in path or "controller" in classname:
        return "Business Logic (Controller)"
    if "service" in path or "service" in classname:
        return "Business Logic (Service)"
    
    if "entity" in path or "entity" in classname:
        return "Boilerplate (Entity)"
    if "config" in path or "config" in classname:
        return "Boilerplate (Config)"
    if "repository" in path or "repository" in classname:
        return "Boilerplate (Repository)"
    if "dto" in path or "dto" in classname:
        return "Boilerplate (DTO)"
    if "init" in path or "init" in classname:
        return "Boilerplate (Init)"
    if "application" in classname:
        return "Boilerplate (App)"
    
    return "Other"

def analyze_distribution():
    stats = defaultdict(lambda: {"count": 0, "loc": 0})
    
    with open(CK_CLASS_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = categorize(row['file'], row['class'])
            stats[category]["count"] += 1
            stats[category]["loc"] += int(row['loc'])
            
    print(f"{'Category':<30} | {'Count':<6} | {'LOC':<10} | {'Avg LOC':<8}")
    print("-" * 65)
    total_count = 0
    total_loc = 0
    for cat, data in sorted(stats.items(), key=lambda x: x[1]['loc'], reverse=True):
        avg = data['loc'] / data['count'] if data['count'] > 0 else 0
        print(f"{cat:<30} | {data['count']:<6} | {data['loc']:<10} | {avg:<8.2f}")
        total_count += data['count']
        total_loc += data['loc']
    
    print("-" * 65)
    print(f"{'Total':<30} | {total_count:<6} | {total_loc:<10} | {total_loc/total_count if total_count > 0 else 0:.2f}")

if __name__ == "__main__":
    analyze_distribution()
