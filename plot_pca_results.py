import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

# Configuration
RESULTS_FILE = "pca_results/pca_results.json"
PLOTS_DIR = "pca_results/plots"

def load_results():
    with open(RESULTS_FILE, 'r') as f:
        return json.load(f)

def plot_scree(data, title, save_path):
    plt.figure(figsize=(10, 5))
    variance = data['variance_ratio']
    cumulative = [sum(variance[:i+1]) for i in range(len(variance))]
    
    plt.bar(range(1, len(variance) + 1), variance, alpha=0.7, label='Individual Variance')
    plt.step(range(1, len(variance) + 1), cumulative, where='mid', label='Cumulative Variance')
    
    plt.xlabel('Principal Components')
    plt.ylabel('Explained Variance Ratio')
    plt.title(title)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_loadings(data, pc_name, title, save_path, top_n=10):
    loadings = pd.Series(data['loadings'][pc_name])
    top_loadings = loadings.abs().sort_values(ascending=False).head(top_n)
    top_loadings_signed = loadings[top_loadings.index]
    
    plt.figure(figsize=(10, 6))
    colors = ['#ff9999' if x < 0 else '#66b3ff' for x in top_loadings_signed]
    top_loadings_signed.plot(kind='barh', color=colors)
    plt.xlabel('Loading Value')
    plt.title(title)
    plt.axvline(x=0, color='black', linestyle='-', linewidth=1)
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def main():
    if not os.path.exists(PLOTS_DIR):
        os.makedirs(PLOTS_DIR)
    
    results = load_results()
    project = results['project_level']
    
    # 1. Class PCA Plots
    print("Generating Class PCA plots...")
    plot_scree(project['class'], 'Scree Plot - Class PCA (Project Level)', f"{PLOTS_DIR}/class_scree.png")
    plot_loadings(project['class'], 'PC1', 'Top 10 Contributors to PC1 (Class)', f"{PLOTS_DIR}/class_pc1_loadings.png")
    plot_loadings(project['class'], 'PC2', 'Top 10 Contributors to PC2 (Class)', f"{PLOTS_DIR}/class_pc2_loadings.png")
    
    # 2. Method PCA Plots
    print("Generating Method PCA plots...")
    plot_scree(project['method'], 'Scree Plot - Method PCA (Project Level)', f"{PLOTS_DIR}/method_scree.png")
    plot_loadings(project['method'], 'PC1', 'Top 10 Contributors to PC1 (Method)', f"{PLOTS_DIR}/method_pc1_loadings.png")
    plot_loadings(project['method'], 'PC2', 'Top 10 Contributors to PC2 (Method)', f"{PLOTS_DIR}/method_pc2_loadings.png")

    print(f"All plots saved in {PLOTS_DIR}")

if __name__ == "__main__":
    main()
