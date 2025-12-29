import json

def generate_html():
    with open('chord_data.json', 'r') as f:
        data = json.load(f)

    data_json_str = json.dumps(data)

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Microservice Interaction Chord Diagram</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #0b0e14;
            color: #e6edf3;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
        }
        header {
            padding: 20px;
            text-align: center;
            width: 100%;
            background: rgba(13, 17, 23, 0.8);
            border-bottom: 1px solid #30363d;
            z-index: 5;
        }
        h1 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 400;
            color: #58a6ff;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        p {
            margin: 5px 0 0 0;
            font-size: 0.9rem;
            color: #8b949e;
        }
        #viz-container {
            flex: 1;
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }
        .tooltip {
            position: absolute;
            padding: 12px;
            background: rgba(22, 27, 34, 0.95);
            border: 1px solid #444c56;
            border-radius: 8px;
            pointer-events: none;
            font-size: 13px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.6);
            z-index: 100;
            display: none;
            backdrop-filter: blur(4px);
        }
        .tooltip strong {
            color: #58a6ff;
        }
        .service-arc {
            cursor: pointer;
            transition: filter 0.2s;
        }
        .service-arc:hover {
            filter: brightness(1.2);
        }
        .method-arc {
            cursor: pointer;
        }
        .chord {
            fill: none;
            stroke-opacity: 0.2;
            transition: stroke-opacity 0.2s, stroke-width 0.2s;
        }
        .chord.active {
            stroke-opacity: 0.9 !important;
            stroke-width: 2.5px !important;
        }
        .chord.inactive {
            stroke-opacity: 0.02 !important;
        }
        .label {
            font-size: 10px;
            fill: #8b949e;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .label.visible {
            opacity: 1;
        }
        .service-label {
            font-size: 11px;
            font-weight: 500;
            fill: #c9d1d9;
            pointer-events: none;
        }
        #controls {
            position: absolute;
            bottom: 20px;
            left: 20px;
            display: flex;
            gap: 10px;
            z-index: 10;
        }
        .btn {
            background: #21262d;
            border: 1px solid #30363d;
            color: #c9d1d9;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        }
        .btn:hover {
            background: #30363d;
            border-color: #8b949e;
        }
    </style>
</head>
<body>
    <header>
        <h1>Microservice Interaction Network</h1>
        <p>A hierarchical chord visualization of service and method dependencies</p>
    </header>
    
    <div id="viz-container">
        <div class="tooltip" id="tooltip"></div>
    </div>

    <div id="controls">
        <button class="btn" id="reset-btn">Reset View</button>
        <button class="btn" id="toggle-labels">Toggle All Labels</button>
    </div>

    <script>
        const data = CHORD_DATA_JSON;

        const width = window.innerWidth;
        const height = window.innerHeight - 100;
        const outerRadius = Math.min(width, height) * 0.45;
        const innerRadius = outerRadius - 30;
        const methodRadius = innerRadius - 10;

        const svg = d3.select("#viz-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", `translate(${width / 2}, ${height / 2})`);

        const tooltip = d3.select("#tooltip");

        // Color scale for services
        const color = d3.scaleOrdinal(d3.schemeCategory10)
            .domain(data.services);

        // Prepare group data for services
        const serviceCounts = {};
        data.nodes.forEach(n => {
            serviceCounts[n.service] = (serviceCounts[n.service] || 0) + 1;
        });

        let startAngle = 0;
        const padding = 0.02; // Padding between services
        const totalMethods = data.nodes.length;
        const anglePerMethod = (2 * Math.PI - padding * data.services.length) / totalMethods;

        // Sort services by method count to group wide services together
        const sortedServices = data.services.slice().sort((a, b) => serviceCounts[b] - serviceCounts[a]);

        const serviceGroups = sortedServices.map(s => {
            const count = serviceCounts[s];
            const group = {
                service: s,
                startAngle: startAngle,
                endAngle: startAngle + count * anglePerMethod,
                count: count
            };
            startAngle = group.endAngle + padding;
            return group;
        });

        // Map methods to angles
        const nodeMap = {};
        sortedServices.forEach(s => {
            const group = serviceGroups.find(g => g.service === s);
            const serviceNodes = data.nodes.filter(n => n.service === s);
            serviceNodes.forEach((n, i) => {
                const angle = group.startAngle + (i + 0.5) * anglePerMethod;
                nodeMap[n.id] = {
                    ...n,
                    angle: angle,
                    group: group
                };
            });
        });

        // Draw Service Arcs
        const arc = d3.arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius)
            .cornerRadius(2);

        const serviceArcs = svg.selectAll(".service-arc")
            .data(serviceGroups)
            .enter()
            .append("path")
            .attr("class", "service-arc")
            .attr("d", arc)
            .attr("fill", d => color(d.service))
            .on("mouseover", function(event, d) {
                tooltip.style("display", "block")
                    .html(`<strong>Service:</strong> ${d.service}<br/><strong>Methods:</strong> ${d.count}`);
                
                highlightService(d.service);
            })
            .on("mousemove", event => {
                tooltip.style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY + 10) + "px");
            })
            .on("mouseout", () => {
                tooltip.style("display", "none");
                resetHighlight();
            });

        // Draw Service Labels (Further out)
        svg.selectAll(".service-label")
            .data(serviceGroups)
            .enter()
            .append("text")
            .attr("class", "service-label")
            .each(function(d) {
                const angle = (d.startAngle + d.endAngle) / 2;
                const r = outerRadius + 45; // Increased distance
                d.x = Math.sin(angle) * r;
                d.y = -Math.cos(angle) * r;
                d.rotation = (angle * 180 / Math.PI);
            })
            .attr("transform", d => `translate(${d.x}, ${d.y}) rotate(${d.rotation > 180 ? d.rotation + 90 : d.rotation - 90})`)
            .attr("text-anchor", d => (d.rotation > 180 ? "start" : "end"))
            .attr("dy", "0.35em")
            .text(d => d.service.replace("ts-", "").replace("-service", ""));

        // Draw Method Labels (Further out from arc)
        const labels = svg.selectAll(".label")
            .data(Object.values(nodeMap))
            .enter()
            .append("text")
            .attr("class", "label")
            .attr("id", d => `label-${d.id}`)
            .each(function(d) {
                const r = innerRadius - 15; // Closer to arc but outside it
                d.x = Math.sin(d.angle) * r;
                d.y = -Math.cos(d.angle) * r;
                d.rotation = (d.angle * 180 / Math.PI);
            })
            .attr("transform", d => `translate(${d.x}, ${d.y}) rotate(${d.rotation > 180 ? d.rotation + 90 : d.rotation - 90})`)
            .attr("text-anchor", d => (d.rotation > 180 ? "start" : "end"))
            .attr("dy", "0.35em")
            .text(d => d.name);

        // Draw Chords
        const ribbon = (d) => {
            const source = nodeMap[d.source];
            const target = nodeMap[d.target];
            const r = innerRadius - 5;
            
            const sx = Math.sin(source.angle) * r;
            const sy = -Math.cos(source.angle) * r;
            const tx = Math.sin(target.angle) * r;
            const ty = -Math.cos(target.angle) * r;

            return `M ${sx} ${sy} Q 0 0 ${tx} ${ty}`;
        };

        const chords = svg.selectAll(".chord")
            .data(data.links)
            .enter()
            .append("path")
            .attr("class", d => `chord source-${d.source} target-${d.target} service-src-${nodeMap[d.source].service} service-tgt-${nodeMap[d.target].service}`)
            .attr("d", ribbon)
            .attr("stroke", d => color(nodeMap[d.source].service))
            .attr("stroke-width", d => Math.log10(d.value + 1) * 2 + 0.5)
            .on("mouseover", function(event, d) {
                const src = nodeMap[d.source];
                const tgt = nodeMap[d.target];
                tooltip.style("display", "block")
                    .html(`<strong>${src.service}</strong><br/>${src.name}<br/>&darr;<br/><strong>${tgt.service}</strong><br/>${tgt.name}<br/>Count: ${d.value}`);
                
                d3.selectAll(".chord").classed("inactive", true);
                d3.select(this).classed("active", true).classed("inactive", false);
                
                d3.select(`#label-${src.id}`).classed("visible", true);
                d3.select(`#label-${tgt.id}`).classed("visible", true);
            })
            .on("mousemove", event => {
                tooltip.style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY + 10) + "px");
            })
            .on("mouseout", () => {
                tooltip.style("display", "none");
                resetHighlight();
            });

        function highlightService(serviceName) {
            d3.selectAll(".chord").classed("inactive", true);
            d3.selectAll(`.service-src-${serviceName}, .service-tgt-${serviceName}`)
                .classed("active", true)
                .classed("inactive", false);
            
            d3.selectAll(".label").classed("visible", false);
            data.nodes.filter(n => n.service === serviceName).forEach(n => {
                d3.select(`#label-${n.id}`).classed("visible", true);
            });
        }

        function resetHighlight() {
            if (!allLabelsVisible) {
                d3.selectAll(".chord").classed("active", false).classed("inactive", false);
                d3.selectAll(".label").classed("visible", false);
            } else {
                d3.selectAll(".chord").classed("active", false).classed("inactive", false);
                d3.selectAll(".label").classed("visible", true);
            }
        }

        let allLabelsVisible = false;
        d3.select("#toggle-labels").on("click", () => {
            allLabelsVisible = !allLabelsVisible;
            d3.selectAll(".label").classed("visible", allLabelsVisible);
        });

        d3.select("#reset-btn").on("click", () => {
            allLabelsVisible = false;
            resetHighlight();
        });

    </script>
</body>
</html>
"""
    final_html = html_template.replace('CHORD_DATA_JSON', data_json_str)
    
    with open('chord_diagram.html', 'w') as f:
        f.write(final_html)
    
    print("Generated chord_diagram.html successfully.")

if __name__ == "__main__":
    generate_html()
