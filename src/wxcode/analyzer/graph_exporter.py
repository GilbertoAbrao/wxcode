"""
Exportador de grafos para formatos de visualização.

Suporta:
- DOT (GraphViz)
- HTML interativo (vis.js)
"""

import json
from pathlib import Path

import networkx as nx


def export_to_dot(graph: nx.DiGraph, output_path: str) -> None:
    """
    Exporta grafo para formato DOT (GraphViz).

    Args:
        graph: Grafo NetworkX
        output_path: Caminho do arquivo de saída
    """
    # Cores por camada
    layer_colors = {
        "schema": "#4CAF50",    # Verde
        "domain": "#2196F3",    # Azul
        "business": "#FF9800",  # Laranja
        "api": "#9C27B0",       # Roxo
        "ui": "#F44336",        # Vermelho
    }

    # Shapes por tipo
    type_shapes = {
        "table": "cylinder",
        "class": "box",
        "procedure": "ellipse",
        "page": "house",
        "window": "house",
        "query": "diamond",
    }

    lines = ["digraph Dependencies {"]
    lines.append("    rankdir=TB;")
    lines.append("    node [style=filled, fontname=\"Arial\"];")
    lines.append("    edge [color=\"#666666\"];")
    lines.append("")

    # Agrupa nós por camada
    layers: dict[str, list[str]] = {}
    for node_id, data in graph.nodes(data=True):
        layer = data.get("layer", "unknown")
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(node_id)

    # Cria subgrafos por camada
    for layer, nodes in layers.items():
        color = layer_colors.get(layer, "#CCCCCC")
        lines.append(f"    subgraph cluster_{layer} {{")
        lines.append(f"        label=\"{layer.upper()}\";")
        lines.append(f"        style=filled;")
        lines.append(f"        color=\"{color}20\";")
        lines.append("")

        for node_id in nodes:
            data = graph.nodes[node_id]
            node_type = data.get("node_type", "unknown")
            shape = type_shapes.get(node_type, "ellipse")
            name = data.get("name", node_id)
            safe_id = node_id.replace(":", "_").replace("-", "_")
            lines.append(
                f"        {safe_id} [label=\"{name}\", "
                f"shape={shape}, fillcolor=\"{color}\"];"
            )

        lines.append("    }")
        lines.append("")

    # Adiciona arestas
    for source, target, data in graph.edges(data=True):
        safe_source = source.replace(":", "_").replace("-", "_")
        safe_target = target.replace(":", "_").replace("-", "_")
        edge_type = data.get("edge_type", "")
        lines.append(f"    {safe_source} -> {safe_target};")

    lines.append("}")

    Path(output_path).write_text("\n".join(lines))


def export_to_html(graph: nx.DiGraph, output_path: str, title: str = "Dependency Graph") -> None:
    """
    Exporta grafo para HTML interativo usando vis.js.

    Args:
        graph: Grafo NetworkX
        output_path: Caminho do arquivo de saída
        title: Título da página
    """
    # Cores por camada
    layer_colors = {
        "schema": {"background": "#4CAF50", "border": "#388E3C"},
        "domain": {"background": "#2196F3", "border": "#1976D2"},
        "business": {"background": "#FF9800", "border": "#F57C00"},
        "api": {"background": "#9C27B0", "border": "#7B1FA2"},
        "ui": {"background": "#F44336", "border": "#D32F2F"},
    }

    # Shapes por tipo
    type_shapes = {
        "table": "database",
        "class": "box",
        "procedure": "ellipse",
        "page": "triangle",
        "window": "triangle",
        "query": "diamond",
    }

    # Prepara dados dos nós
    nodes = []
    for node_id, data in graph.nodes(data=True):
        layer = data.get("layer", "unknown")
        node_type = data.get("node_type", "unknown")
        name = data.get("name", node_id)

        colors = layer_colors.get(layer, {"background": "#CCCCCC", "border": "#999999"})
        shape = type_shapes.get(node_type, "ellipse")

        nodes.append({
            "id": node_id,
            "label": name,
            "group": layer,
            "shape": shape,
            "color": colors,
            "title": f"<b>{name}</b><br>Type: {node_type}<br>Layer: {layer}",
        })

    # Prepara dados das arestas
    edges = []
    for source, target, data in graph.edges(data=True):
        edge_type = data.get("edge_type", "unknown")
        edges.append({
            "from": source,
            "to": target,
            "arrows": "to",
            "title": edge_type,
            "color": {"color": "#666666", "highlight": "#333333"},
        })

    # Gera HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #1a1a2e;
            color: #eee;
        }}
        #header {{
            background: #16213e;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        h1 {{
            margin: 0;
            font-size: 1.5em;
        }}
        #stats {{
            font-size: 0.9em;
            color: #aaa;
        }}
        #legend {{
            display: flex;
            gap: 20px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.85em;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
        }}
        #network {{
            width: 100%;
            height: calc(100vh - 70px);
        }}
        #controls {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #16213e;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        #controls button {{
            background: #0f3460;
            color: #eee;
            border: none;
            padding: 8px 16px;
            margin: 3px;
            border-radius: 4px;
            cursor: pointer;
        }}
        #controls button:hover {{
            background: #1a5f7a;
        }}
        #search {{
            background: #0f3460;
            color: #eee;
            border: 1px solid #1a5f7a;
            padding: 8px 12px;
            border-radius: 4px;
            width: 200px;
            margin-bottom: 10px;
        }}
        #search::placeholder {{
            color: #888;
        }}
        #info {{
            position: fixed;
            top: 80px;
            right: 20px;
            background: #16213e;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            max-width: 300px;
            display: none;
        }}
        #info h3 {{
            margin-top: 0;
            color: #4CAF50;
        }}
        #info .deps {{
            font-size: 0.85em;
            max-height: 200px;
            overflow-y: auto;
        }}
        #info .dep-item {{
            padding: 3px 0;
            border-bottom: 1px solid #333;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🔗 {title}</h1>
        <div id="stats">
            <strong>{len(nodes)}</strong> nodes | <strong>{len(edges)}</strong> edges
        </div>
        <div id="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #4CAF50"></div>
                Schema (tables)
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #2196F3"></div>
                Domain (classes)
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FF9800"></div>
                Business (procedures)
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #F44336"></div>
                UI (pages)
            </div>
        </div>
    </div>

    <div id="network"></div>

    <div id="controls">
        <input type="text" id="search" placeholder="🔍 Search node..." />
        <br>
        <button onclick="network.fit()">📐 Fit All</button>
        <button onclick="togglePhysics()">⚡ Toggle Physics</button>
        <button onclick="filterLayer('all')">All</button>
        <button onclick="filterLayer('schema')">Schema</button>
        <button onclick="filterLayer('domain')">Domain</button>
        <button onclick="filterLayer('business')">Business</button>
        <button onclick="filterLayer('ui')">UI</button>
    </div>

    <div id="info">
        <h3 id="info-title"></h3>
        <div><strong>Type:</strong> <span id="info-type"></span></div>
        <div><strong>Layer:</strong> <span id="info-layer"></span></div>
        <div style="margin-top: 10px"><strong>Dependencies:</strong></div>
        <div class="deps" id="info-deps"></div>
        <div style="margin-top: 10px"><strong>Used by:</strong></div>
        <div class="deps" id="info-usedby"></div>
    </div>

    <script>
        const nodesData = {json.dumps(nodes)};
        const edgesData = {json.dumps(edges)};

        const nodes = new vis.DataSet(nodesData);
        const edges = new vis.DataSet(edgesData);

        const container = document.getElementById('network');
        const data = {{ nodes: nodes, edges: edges }};

        const options = {{
            nodes: {{
                font: {{
                    color: '#ffffff',
                    size: 12
                }},
                borderWidth: 2,
            }},
            edges: {{
                smooth: {{
                    type: 'cubicBezier',
                    forceDirection: 'vertical'
                }},
                width: 1
            }},
            physics: {{
                enabled: true,
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {{
                    gravitationalConstant: -50,
                    centralGravity: 0.01,
                    springLength: 100,
                    springConstant: 0.08
                }},
                stabilization: {{
                    iterations: 200
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100,
                hideEdgesOnDrag: true
            }},
            layout: {{
                improvedLayout: true
            }}
        }};

        const network = new vis.Network(container, data, options);
        let physicsEnabled = true;

        // Search functionality
        document.getElementById('search').addEventListener('input', function(e) {{
            const term = e.target.value.toLowerCase();
            if (term.length < 2) {{
                nodes.forEach(node => {{
                    nodes.update({{id: node.id, hidden: false}});
                }});
                return;
            }}

            nodes.forEach(node => {{
                const matches = node.label.toLowerCase().includes(term);
                nodes.update({{id: node.id, hidden: !matches}});
            }});
        }});

        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            network.setOptions({{ physics: {{ enabled: physicsEnabled }} }});
        }}

        function filterLayer(layer) {{
            nodes.forEach(node => {{
                if (layer === 'all') {{
                    nodes.update({{id: node.id, hidden: false}});
                }} else {{
                    nodes.update({{id: node.id, hidden: node.group !== layer}});
                }}
            }});
        }}

        // Node click handler
        network.on('click', function(params) {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);

                // Get dependencies (outgoing edges)
                const deps = edgesData
                    .filter(e => e.from === nodeId)
                    .map(e => nodes.get(e.to)?.label || e.to);

                // Get used by (incoming edges)
                const usedBy = edgesData
                    .filter(e => e.to === nodeId)
                    .map(e => nodes.get(e.from)?.label || e.from);

                document.getElementById('info-title').textContent = node.label;
                document.getElementById('info-type').textContent = node.shape;
                document.getElementById('info-layer').textContent = node.group;
                document.getElementById('info-deps').innerHTML = deps.length
                    ? deps.map(d => '<div class="dep-item">' + d + '</div>').join('')
                    : '<em>None</em>';
                document.getElementById('info-usedby').innerHTML = usedBy.length
                    ? usedBy.map(d => '<div class="dep-item">' + d + '</div>').join('')
                    : '<em>None</em>';

                document.getElementById('info').style.display = 'block';
            }} else {{
                document.getElementById('info').style.display = 'none';
            }}
        }});

        // Stabilization progress
        network.on('stabilizationProgress', function(params) {{
            console.log('Stabilizing: ' + Math.round(params.iterations/params.total * 100) + '%');
        }});

        network.on('stabilizationIterationsDone', function() {{
            console.log('Stabilization complete');
            network.setOptions({{ physics: {{ enabled: false }} }});
            physicsEnabled = false;
        }});
    </script>
</body>
</html>
"""

    Path(output_path).write_text(html)
