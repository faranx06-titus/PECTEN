from app.physics.circuit_graph import CircuitGraph


def build_circuit_graph(circuit_data):
    """
    Convert PECTEN's Gemini circuit JSON
    into a CircuitGraph.
    """

    graph = CircuitGraph()

    circuit = circuit_data["circuit"]

    components = circuit["components"]
    connections = circuit["connections"]

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

    # ------------------------------------------------
    # Connect terminals according to Gemini output
    # ------------------------------------------------

    for connection in connections:

        from_component = connection["from"]["component"]
        from_terminal = connection["from"]["terminal"]

        to_component = connection["to"]["component"]
        to_terminal = connection["to"]["terminal"]

        from_node = terminal_nodes[
            (from_component, from_terminal)
        ]

        to_node = terminal_nodes[
            (to_component, to_terminal)
        ]

        union(from_node, to_node)

    # ------------------------------------------------
    # Add components to graph
    # ------------------------------------------------

    for component in components:

        component_id = component["id"]
        component_type = component["type"]
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

        graph.add_component(
            component_id,
            component_type,
            value,
            node_1,
            node_2
        )

    return graph