class CircuitReducer:
    """
    Automatically identifies and reduces simple
    series and parallel resistor combinations.
    """

    def __init__(self, graph):
        self.graph = graph
        self.reduction_history = []
    def find_parallel_groups(self):
        """Find resistor components connected between the same two nodes."""

        groups = {}

        for component in self.graph.components.values():

            # Only resistors can be reduced together.
            if component["type"] != "resistor":
                continue

            node_pair = frozenset(
                [component["node1"], component["node2"]]
            )

            groups.setdefault(node_pair, [])

            groups[node_pair].append(
                component["id"]
            )

        return [
            components
            for components in groups.values()
            if len(components) > 1
        ]

    def calculate_parallel_resistance(self, component_ids):
        """Calculate equivalent resistance of a parallel group."""

        inverse_total = 0

        for component_id in component_ids:

            component = self.graph.get_component(
                component_id
            )

            if component["type"] != "resistor":
                raise ValueError(
                    "Only resistors are supported."
                )

            resistance = component["value"]

            if resistance <= 0:
                raise ValueError(
                    f"Invalid resistance: {resistance}"
                )

            inverse_total += 1 / resistance

        return 1 / inverse_total

    def reduce_parallel_group(self, component_ids):
        """
        Replace a parallel group with one equivalent resistor.
        """

        if len(component_ids) < 2:
            raise ValueError(
                "Parallel group needs at least two components."
            )

        first = self.graph.get_component(
            component_ids[0]
        )

        node1 = first["node1"]
        node2 = first["node2"]

        equivalent_resistance = (
            self.calculate_parallel_resistance(
                component_ids
            )
        )

        equivalent_id = (
            "EQ_" + "_".join(component_ids)
        )
        self.reduction_history.append({
            "type": "parallel",
            "components": component_ids.copy(),
            "equivalent": equivalent_id,
            "resistance": equivalent_resistance,
            "node1": node1,
            "node2": node2,
            "component_data": {
                component_id: self.graph.components[
                    component_id
                ].copy()
                for component_id in component_ids
            }
        })

        # Remove old components from graph.
        for component_id in component_ids:

            component = self.graph.components[
                component_id
            ]

            self.graph.nodes[
                component["node1"]
            ].remove(component_id)

            self.graph.nodes[
                component["node2"]
            ].remove(component_id)

            del self.graph.components[
                component_id
            ]
        self.graph.remove_empty_nodes()

        # Add equivalent resistor.
        self.graph.add_component(
            equivalent_id,
            "resistor",
            equivalent_resistance,
            node1,
            node2
        )

        return equivalent_id

    def print_parallel_groups(self):

        groups = self.find_parallel_groups()

        print("===== PARALLEL GROUPS =====")

        if not groups:
            print("No parallel groups found.")
            return

        for index, group in enumerate(
            groups,
            start=1
        ):

            print(
                f"Group {index}: "
                f"{' || '.join(group)}"
            )

    def find_series_groups(self):
         

        groups = []
        visited = set()

        for node_id, component_ids in self.graph.nodes.items():

            if len(component_ids) != 2:
                continue

            first_id = component_ids[0]
            second_id = component_ids[1]

            if first_id in visited or second_id in visited:
                continue

            first = self.graph.get_component(first_id)
            second = self.graph.get_component(second_id)

            if (
                first["type"] == "resistor"
                and second["type"] == "resistor"
            ):
                groups.append(
                    [first_id, second_id]
                )

                visited.add(first_id)
                visited.add(second_id)

        return groups

    def calculate_series_resistance(self, component_ids):
        """Calculate equivalent resistance of a series group."""

        total = 0

        for component_id in component_ids:

            component = self.graph.get_component(
                component_id
            )

            if component["type"] != "resistor":
                raise ValueError(
                    "Only resistors are supported."
                )

            total += component["value"]

        return total

    def reduce_series_group(self, component_ids):
        """Replace a series group with one equivalent resistor."""

        if len(component_ids) < 2:
            raise ValueError(
                "Series group needs at least two components."
            )

        first = self.graph.get_component(
            component_ids[0]
        )

        second = self.graph.get_component(
            component_ids[1]
        )

        # Find the two outer nodes.
        shared_nodes = {
            first["node1"],
            first["node2"]
        }.intersection(
            {
                second["node1"],
                second["node2"]
            }
        )

        if len(shared_nodes) != 1:
            raise ValueError(
                "Components are not connected in series."
            )

        shared_node = next(iter(shared_nodes))

        outer_nodes = []

        for component in [first, second]:

            for node in [
                component["node1"],
                component["node2"]
            ]:

                if node != shared_node:
                    outer_nodes.append(node)

        node1 = outer_nodes[0]
        node2 = outer_nodes[1]

        equivalent_resistance = (
            self.calculate_series_resistance(
                component_ids
            )
        )

        equivalent_id = (
            "EQ_" + "_".join(component_ids)
        )
        self.reduction_history.append({
            "type": "series",
            "components": component_ids.copy(),
            "equivalent": equivalent_id,
            "resistance": equivalent_resistance,
            "node1": node1,
            "node2": node2,
            "component_data": {
                component_id: self.graph.components[
                    component_id
                ].copy()
                for component_id in component_ids
            }
        })    
        # Remove old components.
        for component_id in component_ids:

            component = self.graph.components[
                component_id
            ]

            self.graph.nodes[
                component["node1"]
            ].remove(component_id)

            self.graph.nodes[
                component["node2"]
            ].remove(component_id)

            del self.graph.components[
                component_id
            ]
        self.graph.remove_empty_nodes()

        # Add equivalent resistor.
        self.graph.add_component(
            equivalent_id,
            "resistor",
            equivalent_resistance,
            node1,
            node2
        )

        return equivalent_id

    def reduce_all(self):
        """
        Repeatedly reduce parallel and series resistor groups
        until the circuit cannot be reduced anymore.
        """

        reduction_count = 0

        while True:

            # -----------------------------
            # Try parallel reduction
            # -----------------------------

            parallel_groups = self.find_parallel_groups()

            if parallel_groups:

                group = parallel_groups[0]

                print(
                    f"Reducing parallel group: "
                    f"{' || '.join(group)}"
                )

                self.reduce_parallel_group(group)

                reduction_count += 1

                continue

            # -----------------------------
            # Try series reduction
            # -----------------------------

            series_groups = self.find_series_groups()

            if series_groups:

                group = series_groups[0]

                print(
                    f"Reducing series group: "
                    f"{' + '.join(group)}"
                )

                self.reduce_series_group(group)

                reduction_count += 1

                continue

            # Nothing left to reduce
            break

        print(
            f"\nTotal reductions performed: "
            f"{reduction_count}"
        )

        return reduction_count

    def print_reduction_history(self):

        print("\n===== REDUCTION HISTORY =====")

        for step, record in enumerate(
            self.reduction_history,
            start=1
        ):

            components = record["components"]

            if record["type"] == "parallel":
                operation = " || "
            else:
                operation = " + "

            print(
                f"Step {step}: "
                f"{operation.join(components)} "
                f"→ {record['equivalent']} "
                f"= {record['resistance']} Ω"
            )