import json
import plotly.graph_objects as go
import os

def load_analyzed_services(file_path):
    services = set()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Extract service name from path like ./ts-admin-basic-info-service
                    service_name = line.split('/')[-1]
                    services.add(service_name)
    return services

def extract_interactions(calls, source_service, interactions, analyzed_services, depth=0):
    for call in calls:
        target_service = call.get('service')
        count = call.get('count', 1)
        
        if source_service in analyzed_services and target_service in analyzed_services:
            # Use depth in the key to differentiate colors
            key = (source_service, target_service, depth)
            interactions[key] = interactions.get(key, 0) + count
        
        # Recursively process nested calls with incremented depth
        if call.get('calls'):
            extract_interactions(call['calls'], target_service, interactions, analyzed_services, depth + 1)

def main():
    analyzed_services_file = 'analyzed_services.txt'
    interaction_chain_file = 'interaction_chain.json'
    
    analyzed_services = load_analyzed_services(analyzed_services_file)
    
    with open(interaction_chain_file, 'r') as f:
        chains = json.load(f)
    
    interactions = {}
    for entry in chains:
        source_service = entry.get('service')
        if entry.get('calls'):
            extract_interactions(entry['calls'], source_service, interactions, analyzed_services, depth=0)
    
    # Prepare data for Sankey
    all_nodes = sorted(list(set([s for s, t, d in interactions.keys()] + [t for s, t, d in interactions.keys()])))
    node_indices = {node: i for i, node in enumerate(all_nodes)}
    
    # Define colors for different depths (up to 3)
    depth_names = ["Depth 0 (Root)", "Depth 1", "Depth 2", "Depth 3"]
    depth_colors = [
        'rgba(31, 119, 180, 0.5)',  # Blue
        'rgba(255, 127, 14, 0.5)',  # Orange
        'rgba(44, 160, 44, 0.5)',   # Green
        'rgba(214, 39, 40, 0.5)',   # Red
    ]
    
    sources = []
    targets = []
    values = []
    link_colors = []
    
    for (s, t, d), count in interactions.items():
        sources.append(node_indices[s])
        targets.append(node_indices[t])
        values.append(count)
        link_colors.append(depth_colors[min(d, len(depth_colors) - 1)])
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = all_nodes,
          color = "rgba(100, 100, 100, 0.8)"
        ),
        textfont=dict(size=18),
        link = dict(
          source = sources,
          target = targets,
          value = values,
          color = link_colors,
          hovertemplate = 'Source: %{source.label}<br />' +
                          'Target: %{target.label}<br />' +
                          'Count: %{value}<br />' +
                          'Depth: %{customdata}<extra></extra>',
          customdata = [d for s, t, d in interactions.keys()]
        ))])

    # Create larger legend items horizontally at the top-right
    legend_annotations = []
    
    
    # Horizontal spacing between legend items
    for i, (name, color) in enumerate(zip(depth_names, depth_colors)):
        # Calculate x position for horizontal layout (moving to the left from the right edge)
        # i=0 (Root) will be leftmost, i=3 will be rightmost
        x_pos = 0.55 + (i * 0.12) 
        
        legend_annotations.append(dict(
            x=x_pos, y=1.05,
            xref="paper", yref="paper",
            text=f'<span style="color:{color.replace("0.5", "1.0")}; font-size: 24px;">■</span> {name}',
            showarrow=False,
            xanchor="left",
            font=dict(size=16)
        ))

    fig.update_layout(
        title=dict(text="Microservice Interaction Sankey Diagram (Max Depth 3)", font=dict(size=24)),
        font_size=14,
        annotations=legend_annotations,
        margin=dict(r=50, t=130, l=50, b=50) # Increased top margin for horizontal legend
    )
    
    # Save as HTML
    fig.write_html("microservice_sankey.html")
    print("Sankey diagram saved as microservice_sankey.html")
    
    # Save as Static Image
    try:
        fig.write_image("microservice_sankey.png")
        print("Sankey diagram saved as microservice_sankey.png")
    except Exception as e:
        print(f"Could not save static image: {e}")

if __name__ == "__main__":
    main()
