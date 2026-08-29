class CircuitGraph:
    """
    Represents a circuit as a graph.

    Nodes = electrical junctions
    Components = battery, resistor, etc.
    """

    def __init__(self):
        self.nodes = {}
        self.components = {}

    def add_node(self, node_id):
        """Add an electrical node."""

        if node_id not in self.nodes:
            self.nodes[node_id] = []

    def add_component(
        self,
        component_id,
        component_type,
        value=None,
        node1=None,
        node2=None
    ):
        """Add a circuit component between two nodes."""

        if node1 is None or node2 is None:
            raise ValueError(
                f"Component {component_id} needs two nodes."
            )

        self.add_node(node1)
        self.add_node(node2)

        component = {
            "id": component_id,
            "type": component_type,
            "value": value,
            "node1": node1,
            "node2": node2
        }

        self.components[component_id] = component

        self.nodes[node1].append(component_id)
        self.nodes[node2].append(component_id)

    def get_node_components(self, node_id):
        """Return components connected to a node."""

        if node_id not in self.nodes:
            raise ValueError(
                f"Unknown node: {node_id}"
            )

        return self.nodes[node_id]

    def get_component(self, component_id):
        """Return component information."""

        if component_id not in self.components:
            raise ValueError(
                f"Unknown component: {component_id}"
            )

        return self.components[component_id]

    def print_graph(self):
        """Print the circuit graph."""

        print("===== CIRCUIT GRAPH =====")

        print("\nNODES:")

        for node_id, components in self.nodes.items():
            print(
                f"{node_id}: {components}"
            )

        print("\nCOMPONENTS:")

        for component in self.components.values():
            print(
                f"{component['id']}: "
                f"{component['type']} "
                f"({component['node1']} ↔ "
                f"{component['node2']})"
            )
    def remove_empty_nodes(self):
        """Remove nodes that no longer contain components."""

        empty_nodes = [
            node_id
            for node_id, components in self.nodes.items()
            if not components
        ]

        for node_id in empty_nodes:
            del self.nodes[node_id]