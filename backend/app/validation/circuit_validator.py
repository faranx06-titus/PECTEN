import math


def validate_circuit(circuit_data):
    if not isinstance(circuit_data, dict):
        return ["Circuit data must be an object."]
    errors = []

    if "circuit" not in circuit_data:
        errors.append("Missing circuit data.")
        return errors

    circuit = circuit_data.get("circuit")
    if not isinstance(circuit, dict):
        return ["Circuit must be an object."]

    if "components" not in circuit:
        errors.append("Missing components.")
        return errors

    components = circuit["components"]

    if not isinstance(components, list):
        return ["Components must be a list."]
    if not components:
        errors.append("Circuit contains no components.")

    component_ids = set()

    for component in components:
        if not isinstance(component, dict):
            errors.append("Each component must be an object.")
            continue
        component_id = component.get("id")
        component_type = component.get("type")

        if not component_id:
            errors.append("Component is missing an ID.")
            continue

        if component_id in component_ids:
            errors.append(f"Duplicate component ID: {component_id}")

        component_ids.add(component_id)

        if not component_type:
            errors.append(f"{component_id} is missing its type.")
        elif component_type not in ("resistor", "bulb", "battery", "cell", "wire"):
            errors.append(f"{component_id} has unsupported component type: {component_type}.")

        if "terminals" not in component:
            errors.append(f"{component_id} is missing terminals.")
        elif (not isinstance(component["terminals"], list)
              or len(component["terminals"]) != 2
              or not all(isinstance(terminal, str) for terminal in component["terminals"])):
            errors.append(f"{component_id} must have exactly two terminals.")

        if component_type in ("resistor", "bulb"):
            value = component.get("value")
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                errors.append(f"{component_id} must have a positive resistance value.")
        elif component_type in ("battery", "cell"):
            value = component.get("value")
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                errors.append(f"{component_id} must have a positive voltage value.")

    nodes = circuit.get("nodes")
    if nodes is not None:
        if not isinstance(nodes, list) or not nodes:
            errors.append("Circuit nodes must be a non-empty list when provided.")
        else:
            assigned_terminals = set()
            for node in nodes:
                if not isinstance(node, dict) or not isinstance(node.get("terminals"), list) or not node["terminals"]:
                    errors.append("Each circuit node must contain at least one terminal.")
                    continue
                for endpoint in node["terminals"]:
                    if not isinstance(endpoint, dict):
                        errors.append("Node terminals must be endpoint objects.")
                        continue
                    comp_id = endpoint.get("component")
                    matching = next((item for item in components if item.get("id") == comp_id), None)
                    if not matching or endpoint.get("terminal") not in matching.get("terminals", []):
                        errors.append(f"Circuit node references an unknown terminal: {comp_id} {endpoint.get('terminal')}.")
                        continue
                    key = (comp_id, endpoint["terminal"])
                    if key in assigned_terminals:
                        errors.append(f"Terminal {comp_id} {endpoint['terminal']} belongs to more than one node.")
                    assigned_terminals.add(key)
            expected_terminals = {
                (component.get("id"), terminal)
                for component in components
                for terminal in (component.get("terminals") if isinstance(component.get("terminals"), list) else [])
            }
            if assigned_terminals != expected_terminals:
                errors.append("Every component terminal must belong to exactly one circuit node.")

    if "connections" not in circuit and nodes is None:
        errors.append("Missing connections.")
        return errors

    connections = circuit.get("connections", [])
    if not isinstance(connections, list):
        return errors + ["Connections must be a list."]

    for connection in connections:
        if not isinstance(connection, dict):
            errors.append("Each connection must be an object.")
            continue
        from_data = connection.get("from") or {}
        to_data = connection.get("to") or {}
        if not isinstance(from_data, dict) or not isinstance(to_data, dict):
            errors.append("Connection endpoints must be objects.")
            continue

        from_component = from_data.get("component")
        to_component = to_data.get("component")

        if from_component not in component_ids:
            errors.append(
                f"Connection references unknown component: {from_component}"
            )

        if to_component not in component_ids:
            errors.append(
                f"Connection references unknown component: {to_component}"
            )

        for endpoint, comp_id in ((from_data, from_component), (to_data, to_component)):
            matching = next((c for c in components if c.get("id") == comp_id), None)
            terminals = matching.get("terminals") if matching else None
            if isinstance(terminals, list) and endpoint.get("terminal") not in terminals:
                errors.append(f"Connection references unknown terminal on component: {comp_id}")

    return errors
