from app.physics.graph_builder import build_circuit_graph
from app.physics.circuit_reducer import CircuitReducer
from app.physics.circuit_solver import CircuitSolver
from app.validation.circuit_validator import validate_circuit
from copy import deepcopy


def solve_circuit_data(data):
    """Validate and solve the nested circuit representation shared by the API."""
    if "circuit" not in data and "components" in data:
        data = {"circuit": data}

    errors = validate_circuit(data)
    if errors:
        raise ValueError(" ".join(errors))

    # The graph builder consumes this same nested representation for Gemini and UI edits.
    graph = build_circuit_graph(data)
    topology_check = inspect_topology(graph)
    if not topology_check["passed"]:
        messages = " ".join(item["message"] for item in topology_check["warnings"])
        raise ValueError(messages)
    solution = CircuitSolver(graph).solve_total_current()
    # Keep reduction history as a human-readable hint while calculation uses
    # the unmodified network graph solved by nodal analysis.
    reducer = CircuitReducer(deepcopy(graph))
    reducer.reduce_all()
    solution["reduction_history"] = reducer.reduction_history
    solution["wire_currents"] = calculate_wire_currents(data, graph, solution)
    solution["kcl_check"] = calculate_kcl_check(graph, solution)
    solution["physics_checks"] = calculate_physics_checks(graph, solution)
    solution["topology_check"] = topology_check
    if not solution["physics_checks"]["passed"]:
        failed = ", ".join(
            name for name, check in solution["physics_checks"]["checks"].items()
            if not check["passed"]
        )
        raise ValueError(f"The calculated circuit did not pass its physics checks ({failed}). Check the circuit connections and values.")
    return graph, reducer, solution


def inspect_topology(graph):
    """Report suspicious open ends and disconnected islands for student review."""
    warnings = []
    batteries = [item for item in graph.components.values() if item["type"] == "battery"]
    for battery in batteries:
        if battery["node1"] == battery["node2"]:
            warnings.append({"kind": "battery_short", "component": battery["id"],
                             "message": f"Both {battery['id']} terminals are on the same connection. Check the wire connections."})

    for node_id, component_ids in graph.nodes.items():
        if len(component_ids) == 1:
            component = graph.components[component_ids[0]]
            terminal = "1" if component["node1"] == node_id else "2"
            warnings.append({
                "kind": "open_end",
                "node": node_id,
                "component": component["id"],
                "terminal": terminal,
                "message": f"{component['id']} end {terminal} is not shown connected to another component.",
            })

    unseen = set(graph.nodes)
    islands = 0
    while unseen:
        islands += 1
        pending = [unseen.pop()]
        while pending:
            node_id = pending.pop()
            for component_id in graph.nodes[node_id]:
                component = graph.components[component_id]
                other = component["node2"] if component["node1"] == node_id else component["node1"]
                if other in unseen:
                    unseen.remove(other)
                    pending.append(other)
    if islands > 1:
        warnings.append({"kind": "disconnected_islands", "count": islands,
                         "message": f"The detected circuit has {islands} disconnected sections. Check whether a wire was missed."})
    return {"passed": not any(item["kind"] in ("battery_short", "disconnected_islands") for item in warnings),
            "connected_sections": islands, "warnings": warnings}


def calculate_kcl_check(graph, solution):
    """Check that solved terminal currents balance at every electrical node."""
    residuals = {}
    for node_id in graph.nodes:
        current_sum = 0.0
        for component_id in graph.nodes[node_id]:
            component = graph.components[component_id]
            result = solution["components"].get(component_id)
            if not result:
                continue
            current = result["current"]
            current_sum += current if component["node1"] == node_id else -current
        residuals[node_id] = current_sum

    scale = max(1.0, *(abs(value) for value in residuals.values()))
    tolerance = 1e-7 * scale
    maximum = max((abs(value) for value in residuals.values()), default=0.0)
    return {
        "passed": maximum <= tolerance,
        "max_node_residual": maximum,
        "tolerance": tolerance,
        "node_residuals": residuals,
    }


def calculate_physics_checks(graph, solution):
    """Verify branch Ohm's law and power balance against the nodal solution."""
    kcl = solution["kcl_check"]
    ohm_residuals = {}
    for component_id, component in graph.components.items():
        if component["type"] not in ("resistor", "bulb"):
            continue
        result = solution["components"][component_id]
        ohm_residuals[component_id] = result["current"] - result["voltage"] / component["value"]

    current_scale = max(1.0, *(abs(item) for item in ohm_residuals.values()))
    current_tolerance = 1e-8 * current_scale
    max_ohm_residual = max((abs(item) for item in ohm_residuals.values()), default=0.0)

    total_power = sum(item["power"] for item in solution["components"].values())
    power_scale = max(1.0, *(abs(item["power"]) for item in solution["components"].values()))
    power_tolerance = 1e-8 * power_scale
    checks = {
        "kirchhoff_current_law": {
            "passed": kcl["passed"],
            "residual": kcl["max_node_residual"],
            "tolerance": kcl["tolerance"],
        },
        "ohms_law": {
            "passed": max_ohm_residual <= current_tolerance,
            "residual": max_ohm_residual,
            "tolerance": current_tolerance,
            "component_residuals": ohm_residuals,
        },
        "power_balance": {
            "passed": abs(total_power) <= power_tolerance,
            "residual": total_power,
            "tolerance": power_tolerance,
        },
    }
    return {"passed": all(check["passed"] for check in checks.values()), "checks": checks}


def calculate_wire_currents(data, graph, solution):
    """Route solved terminal currents through traced wire paths while preserving KCL.

    A junction can have several valid internal wire-current distributions because
    ideal wires have zero resistance. For animation, choose a deterministic
    spanning tree for each traced wire network and solve its edge currents from
    the component-terminal current injections. This gives a KCL-consistent
    visualization without claiming that currents inside an ideal junction are
    physically unique.
    """
    circuit = data.get("circuit", {})
    components = {component.get("id"): component for component in circuit.get("components", [])}
    ports_by_node = {}
    for (component_id, terminal), node in graph.terminal_nodes.items():
        if components.get(component_id, {}).get("type") not in ("wire", "junction"):
            ports_by_node.setdefault(node, set()).add((component_id, terminal))

    def terminal_current_out(component_id, node):
        component = graph.components.get(component_id)
        result = solution["components"].get(component_id)
        if not component or not result:
            return None
        current = result["current"]
        if node == component["node1"]:
            return -current
        if node == component["node2"]:
            return current
        return None

    wire_paths = (data.get("visual") or {}).get("wire_paths", [])
    wire_records = []
    edges_by_node = {}
    for index, wire in enumerate(wire_paths):
        start = (wire.get("from_component"), wire.get("from_terminal"))
        end = (wire.get("to_component"), wire.get("to_terminal"))
        node_start = graph.terminal_nodes.get(start)
        node_end = graph.terminal_nodes.get(end)
        wire_records.append({"current": None, "resolved": False})
        if node_start is not None and node_start == node_end and start != end:
            edges_by_node.setdefault(node_start, []).append((index, start, end))

    tolerance = 1e-7
    for node, edges in edges_by_node.items():
        adjacency = {}
        for edge_index, start, end in edges:
            adjacency.setdefault(start, []).append((end, edge_index))
            adjacency.setdefault(end, []).append((start, edge_index))

        injections = {}
        for port in ports_by_node.get(node, ()):
            value = terminal_current_out(port[0], node)
            if value is not None:
                injections[port] = value

        visited = set()
        for root in adjacency:
            if root in visited:
                continue
            parent = {root: None}
            parent_edge = {}
            order = [root]
            visited.add(root)
            for port in order:
                for neighbor, edge_index in adjacency.get(port, ()):
                    if neighbor in visited:
                        continue
                    visited.add(neighbor)
                    parent[neighbor] = port
                    parent_edge[neighbor] = edge_index
                    order.append(neighbor)

            subtree_current = {port: injections.get(port, 0.0) for port in order}
            for port in reversed(order[1:]):
                edge_index = parent_edge[port]
                wire = wire_paths[edge_index]
                edge_start = (wire.get("from_component"), wire.get("from_terminal"))
                edge_end = (wire.get("to_component"), wire.get("to_terminal"))
                # Positive wire current follows the path's declared start-to-end order.
                current = subtree_current[port] if port == edge_start else -subtree_current[port]
                wire_records[edge_index] = {"current": current, "resolved": True}
                subtree_current[parent[port]] += subtree_current[port]

            component_injection = sum(injections.get(port, 0.0) for port in order)
            scale = max(1.0, *(abs(injections.get(port, 0.0)) for port in order))
            if abs(component_injection) > tolerance * scale:
                for port in order[1:]:
                    wire_records[parent_edge[port]] = {"current": None, "resolved": False}

    return wire_records
