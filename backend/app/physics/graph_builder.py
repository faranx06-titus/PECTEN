from app.physics.circuit_graph import CircuitGraph


def build_circuit_graph(circuit_data):
    """
    Convert PECTEN's Gemini circuit JSON
    into a CircuitGraph.
    """

    graph = CircuitGraph()

    circuit = circuit_data["circuit"]

    components = circuit["components"]
    connections = circuit.get("connections", [])

    # ------------------------------------------------
    # Create a unique node for every terminal
    # ------------------------------------------------

    terminal_nodes = {}

    for component in components:
        component_id = component["id"]
        terminals = component["terminals"]

        for terminal in terminals:

            key = (
                component_id,
                terminal
            )

            terminal_nodes[key] = (
                f"{component_id}_{terminal}"
            )

    # ------------------------------------------------
    # Union connected terminals
    # ------------------------------------------------

    parent = {
        node: node
        for node in terminal_nodes.values()
    }

    def find(node):

        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]

        return node

    def union(a, b):

        root_a = find(a)
        root_b = find(b)

        if root_a != root_b:
            parent[root_b] = root_a

    # Explicit wire components always short their own two terminals.
    for component in components:
        if component.get("type") == "wire":
            terminals = component.get("terminals", [])
            if len(terminals) == 2:
                union(terminal_nodes[(component["id"], terminals[0])],
                      terminal_nodes[(component["id"], terminals[1])])

    if circuit.get("nodes") is not None:
        # Explicit node groups are the reviewable topology source of truth.
        for node in circuit["nodes"]:
            endpoints = node.get("terminals", [])
            if endpoints:
                first = endpoints[0]
                for endpoint in endpoints[1:]:
                    union(
                        terminal_nodes[(first["component"], first["terminal"])],
                        terminal_nodes[(endpoint["component"], endpoint["terminal"])],
                    )
    else:
        # Legacy connection pairs remain supported for older API callers.
        for connection in connections:
            from_node = terminal_nodes[(connection["from"]["component"], connection["from"]["terminal"])]
            to_node = terminal_nodes[(connection["to"]["component"], connection["to"]["terminal"])]
            union(from_node, to_node)

    graph.terminal_nodes = {
        key: find(raw_node) for key, raw_node in terminal_nodes.items()
    }

    # ------------------------------------------------
    # Add components to graph
    # ------------------------------------------------

    for component in components:
        if component["type"] == "wire":
            continue

        component_id = component["id"]
        component_type = component["type"]
        if component_type == "cell":
            component_type = "battery"
        value = component.get("value")

        terminal_1 = component["terminals"][0]
        terminal_2 = component["terminals"][1]

        raw_node_1 = terminal_nodes[
            (component_id, terminal_1)
        ]

        raw_node_2 = terminal_nodes[
            (component_id, terminal_2)
        ]

        node_1 = find(raw_node_1)
        node_2 = find(raw_node_2)

        polarity = component.get("polarity") or {}
        terminal_1_polarity = str(polarity.get("terminal_1", "")).lower()
        terminal_2_polarity = str(polarity.get("terminal_2", "")).lower()
        if terminal_1_polarity in ("negative", "-") or terminal_2_polarity in ("positive", "+"):
            node_1, node_2 = node_2, node_1

        graph.add_component(
            component_id,
            component_type,
            value,
            node_1,
            node_2
        )

    return graph
