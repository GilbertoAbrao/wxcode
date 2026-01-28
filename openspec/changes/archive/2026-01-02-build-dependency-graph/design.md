# Design: build-dependency-graph

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      DependencyAnalyzer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ GraphBuilder │  │ CycleDetector│  │ TopologicalSorter   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│         │                 │                    │                 │
│         ▼                 ▼                    ▼                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              NetworkX DiGraph                            │    │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐         │    │
│  │  │ Tables │→ │Classes │→ │Procs   │→ │ Pages  │         │    │
│  │  └────────┘  └────────┘  └────────┘  └────────┘         │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │    MongoDB       │
                    │ (update order)   │
                    └──────────────────┘
```

## Data Model

### GraphNode (Pydantic)
```python
class NodeType(str, Enum):
    TABLE = "table"
    CLASS = "class"
    PROCEDURE = "procedure"
    PAGE = "page"
    QUERY = "query"

class GraphNode(BaseModel):
    id: str                    # Unique ID (collection:_id)
    name: str                  # Display name
    node_type: NodeType
    layer: ElementLayer        # schema, domain, business, ui
    mongo_id: PydanticObjectId # Reference to MongoDB document
    collection: str            # MongoDB collection name
```

### GraphEdge (Pydantic)
```python
class EdgeType(str, Enum):
    INHERITS = "inherits"           # Class → Class (herança)
    USES_CLASS = "uses_class"       # Any → Class
    CALLS_PROCEDURE = "calls_proc"  # Any → Procedure
    USES_TABLE = "uses_table"       # Any → Table
    USES_QUERY = "uses_query"       # Any → Query

class GraphEdge(BaseModel):
    source: str      # Node ID
    target: str      # Node ID
    edge_type: EdgeType
    weight: int = 1  # For importance ranking
```

### AnalysisResult (Pydantic)
```python
class CycleInfo(BaseModel):
    nodes: list[str]
    suggested_break: str  # Node to remove to break cycle

class AnalysisResult(BaseModel):
    total_nodes: int
    total_edges: int
    nodes_by_type: dict[NodeType, int]
    edges_by_type: dict[EdgeType, int]
    cycles: list[CycleInfo]
    has_cycles: bool
    topological_order: list[str]  # Node IDs in order
    layers: dict[ElementLayer, list[str]]
```

## Algorithm

### 1. Graph Construction
```python
async def build_graph(project_id: ObjectId) -> nx.DiGraph:
    graph = nx.DiGraph()

    # 1. Add table nodes (from schema)
    schema = await DatabaseSchema.find_one({"project_id": project_id})
    for table in schema.tables:
        graph.add_node(f"table:{table.name}",
                       node_type=NodeType.TABLE,
                       layer=ElementLayer.SCHEMA)

    # 2. Add class nodes
    classes = await ClassDefinition.find({"project_id": project_id}).to_list()
    for cls in classes:
        graph.add_node(f"class:{cls.name}",
                       node_type=NodeType.CLASS,
                       layer=ElementLayer.DOMAIN)

        # Edge: inheritance
        if cls.inherits_from:
            graph.add_edge(f"class:{cls.name}",
                          f"class:{cls.inherits_from}",
                          edge_type=EdgeType.INHERITS)

        # Edge: uses tables
        for table in cls.dependencies.uses_files:
            graph.add_edge(f"class:{cls.name}",
                          f"table:{table}",
                          edge_type=EdgeType.USES_TABLE)

    # 3. Add procedure nodes
    procedures = await Procedure.find({"project_id": project_id}).to_list()
    for proc in procedures:
        graph.add_node(f"proc:{proc.name}",
                       node_type=NodeType.PROCEDURE,
                       layer=ElementLayer.BUSINESS)

        # Edge: calls other procedures
        for called in proc.dependencies.calls_procedures:
            if called != proc.name:  # Ignore self-recursion
                graph.add_edge(f"proc:{proc.name}",
                              f"proc:{called}",
                              edge_type=EdgeType.CALLS_PROCEDURE)

        # Edge: uses tables
        for table in proc.dependencies.uses_files:
            graph.add_edge(f"proc:{proc.name}",
                          f"table:{table}",
                          edge_type=EdgeType.USES_TABLE)

    # 4. Add page nodes (from elements)
    pages = await Element.find({
        "project_id": project_id,
        "source_type": ElementType.PAGE
    }).to_list()
    for page in pages:
        graph.add_node(f"page:{page.source_name}",
                       node_type=NodeType.PAGE,
                       layer=ElementLayer.UI)

        # Edge: uses procedures/classes
        for dep in page.dependencies.uses:
            if dep.startswith("class"):
                graph.add_edge(f"page:{page.source_name}",
                              f"class:{dep}",
                              edge_type=EdgeType.USES_CLASS)
            else:
                graph.add_edge(f"page:{page.source_name}",
                              f"proc:{dep}",
                              edge_type=EdgeType.CALLS_PROCEDURE)

    return graph
```

### 2. Cycle Detection
```python
def detect_cycles(graph: nx.DiGraph) -> list[CycleInfo]:
    cycles = []
    try:
        cycle_nodes = nx.find_cycle(graph)
        # Find all simple cycles
        for cycle in nx.simple_cycles(graph):
            cycles.append(CycleInfo(
                nodes=cycle,
                suggested_break=_find_best_break_point(graph, cycle)
            ))
    except nx.NetworkXNoCycle:
        pass  # No cycles - good!

    return cycles

def _find_best_break_point(graph: nx.DiGraph, cycle: list[str]) -> str:
    """Find node with lowest in-degree to break cycle."""
    min_degree = float('inf')
    best_node = cycle[0]
    for node in cycle:
        if graph.in_degree(node) < min_degree:
            min_degree = graph.in_degree(node)
            best_node = node
    return best_node
```

### 3. Topological Sort with Layers
```python
def compute_topological_order(graph: nx.DiGraph) -> tuple[list[str], dict]:
    """
    Computes topological order respecting layers.

    Order: Tables → Classes (by inheritance depth) → Procedures → Pages
    """
    # Handle cycles by temporarily removing back edges
    if not nx.is_directed_acyclic_graph(graph):
        graph = _remove_cycle_edges(graph)

    # Sort within each layer
    layers = {
        ElementLayer.SCHEMA: [],
        ElementLayer.DOMAIN: [],
        ElementLayer.BUSINESS: [],
        ElementLayer.UI: [],
    }

    for node in graph.nodes():
        layer = graph.nodes[node].get('layer')
        layers[layer].append(node)

    # Topological sort within each layer
    order = []
    current_order = 0
    order_map = {}

    for layer in [ElementLayer.SCHEMA, ElementLayer.DOMAIN,
                  ElementLayer.BUSINESS, ElementLayer.UI]:
        subgraph = graph.subgraph(layers[layer])
        layer_order = list(nx.topological_sort(subgraph))

        for node in layer_order:
            order.append(node)
            order_map[node] = current_order
            current_order += 1

    return order, order_map
```

### 4. Persistence
```python
async def persist_order(project_id: ObjectId, order_map: dict[str, int]):
    """Update topological_order in all collections."""

    # Update classes
    for node_id, order in order_map.items():
        if node_id.startswith("class:"):
            name = node_id.split(":")[1]
            await ClassDefinition.find_one({
                "project_id": project_id,
                "name": name
            }).update({"$set": {"topological_order": order}})

    # Update procedures
    for node_id, order in order_map.items():
        if node_id.startswith("proc:"):
            name = node_id.split(":")[1]
            await Procedure.find_one({
                "project_id": project_id,
                "name": name
            }).update({"$set": {"topological_order": order}})

    # Update elements (pages)
    for node_id, order in order_map.items():
        if node_id.startswith("page:"):
            name = node_id.split(":")[1]
            await Element.find_one({
                "project_id": project_id,
                "source_name": name
            }).update({"$set": {
                "topological_order": order,
                "layer": ElementLayer.UI
            }})
```

## File Structure
```
src/wxcode/analyzer/
├── __init__.py
├── dependency_graph.py      # DependencyGraph class
├── graph_builder.py         # Build graph from MongoDB
├── cycle_detector.py        # Detect and handle cycles
├── topological_sorter.py    # Compute order with layers
├── models.py                # GraphNode, GraphEdge, AnalysisResult
└── visualizer.py            # Optional: generate graph images
```

## CLI Integration
```python
# In cli.py
@app.command("analyze-deps")
def analyze_deps(
    project_dir: Path = typer.Argument(...),
    visualize: bool = typer.Option(False, help="Generate graph visualization"),
    export_dot: bool = typer.Option(False, help="Export to GraphViz DOT"),
    show_cycles: bool = typer.Option(False, help="Show detected cycles"),
    dry_run: bool = typer.Option(False, help="Don't persist to MongoDB"),
):
    """Analyze dependencies and compute conversion order."""
    ...
```

## Trade-offs

### NetworkX vs Custom Implementation
- **Chose NetworkX**: Mature library with well-tested algorithms
- **Trade-off**: Additional dependency, but saves significant development time
- **Alternative**: Custom adjacency list (more control, more code)

### Handling Cycles
- **Approach 1**: Error and abort (strict)
- **Approach 2**: Warn and suggest breaks (chosen)
- **Approach 3**: Automatically break cycles
- **Chose Approach 2**: User should decide how to handle cycles

### Layer Assignment
- **Approach 1**: Fixed by file type (chosen - simpler)
- **Approach 2**: Dynamic based on dependencies (complex)
- **Chose Approach 1**: File type is a reliable indicator of layer

## Performance Considerations
- Load all data in memory (acceptable for ~1000 elements)
- Use batch updates for MongoDB persistence
- NetworkX algorithms are O(V+E) for topological sort
- Cycle detection is O(V+E) with DFS
