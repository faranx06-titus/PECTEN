def validate_circuit(circuit_data):
    errors = []

    if "circuit" not in circuit_data:
        errors.append("Missing circuit data.")
        return errors

    circuit = circuit_data["circuit"]

    if "components" not in circuit:
        errors.append("Missing components.")
        return errors

    components = circuit["components"]

    if len(components) == 0:
        errors.append("Circuit contains no components.")

    component_ids = set()

    for component in components:
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

        if "terminals" not in component:
            errors.append(f"{component_id} is missing terminals.")

    if "connections" not in circuit:
        errors.append("Missing connections.")
        return errors

    connections = circuit["connections"]

    for connection in connections:
        from_data = connection.get("from", {})
        to_data = connection.get("to", {})

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

    return errors