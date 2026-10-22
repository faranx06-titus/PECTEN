class CircuitSolver:
    """Solve a connected resistive network with ideal voltage sources using MNA."""

    def __init__(self, graph):
        self.graph = graph

    def find_batteries(self):
        batteries = [
            component for component in self.graph.components.values()
            if component["type"] == "battery"
        ]
        if not batteries:
            raise ValueError("The circuit must contain a battery to have current.")
        return batteries

    @staticmethod
    def _solve_linear_system(matrix, rhs):
        """Gaussian elimination with partial pivoting."""
        size = len(rhs)
        augmented = [row[:] + [rhs[index]] for index, row in enumerate(matrix)]
        for column in range(size):
            pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
            if abs(augmented[pivot][column]) < 1e-12:
                raise ValueError("Circuit is open, disconnected, or otherwise unsolvable.")
            augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
            scale = augmented[column][column]
            augmented[column] = [value / scale for value in augmented[column]]
            for row in range(size):
                if row == column:
                    continue
                factor = augmented[row][column]
                if factor:
                    augmented[row] = [
                        value - factor * pivot_value
                        for value, pivot_value in zip(augmented[row], augmented[column])
                    ]
        return [augmented[row][-1] for row in range(size)]

    def solve_total_current(self):
        batteries = self.find_batteries()
        source_groups = []
        for battery in batteries:
            matching_group = next((group for group in source_groups
                                   if (group[0]["node1"], group[0]["node2"]) in
                                   ((battery["node1"], battery["node2"]), (battery["node2"], battery["node1"]))), None)
            if matching_group is None:
                source_groups.append([battery])
                continue
            representative = matching_group[0]
            same_orientation = (representative["node1"], representative["node2"]) == (battery["node1"], battery["node2"])
            same_voltage = abs(float(representative["value"]) - float(battery["value"])) <= 1e-9
            if not (same_orientation and same_voltage):
                raise ValueError(
                    f"{representative['id']} and {battery['id']} are ideal sources connected in parallel with different polarity or voltage. "
                    "Real batteries need internal resistance to model this connection."
                )
            matching_group.append(battery)
        resistors = [
            component for component in self.graph.components.values()
            if component["type"] in ("resistor", "bulb")
        ]
        if not resistors:
            raise ValueError("The circuit must contain at least one resistor or bulb.")

        # Each independent ideal-source group adds one MNA current variable
        # and voltage constraint. Identical parallel cells share that group
        # current equally as a stated symmetry assumption.
        reference = batteries[0]["node2"]
        unknown_nodes = [node for node in self.graph.nodes if node != reference]
        node_index = {node: index for index, node in enumerate(unknown_nodes)}
        source_indices = {
            battery["id"]: len(unknown_nodes) + index
            for index, battery in enumerate(group[0] for group in source_groups)
        }
        size = len(unknown_nodes) + len(source_groups)
        matrix = [[0.0] * size for _ in range(size)]
        rhs = [0.0] * size

        def stamp_conductance(node_a, node_b, conductance):
            a = node_index.get(node_a)
            b = node_index.get(node_b)
            if a is not None:
                matrix[a][a] += conductance
            if b is not None:
                matrix[b][b] += conductance
            if a is not None and b is not None:
                matrix[a][b] -= conductance
                matrix[b][a] -= conductance

        for component in resistors:
            resistance = component["value"]
            if resistance <= 0:
                raise ValueError(f"{component['id']} resistance must be greater than zero.")
            stamp_conductance(component["node1"], component["node2"], 1.0 / resistance)

        for group in source_groups:
            battery = group[0]
            source_index = source_indices[battery["id"]]
            positive = node_index.get(battery["node1"])
            negative = node_index.get(battery["node2"])
            if positive is not None:
                matrix[positive][source_index] += 1.0
                matrix[source_index][positive] += 1.0
            if negative is not None:
                matrix[negative][source_index] -= 1.0
                matrix[source_index][negative] -= 1.0
            rhs[source_index] = battery["value"]

        values = self._solve_linear_system(matrix, rhs)
        node_voltages = {reference: 0.0}
        node_voltages.update({node: values[index] for node, index in node_index.items()})
        component_results = {}
        for component in resistors:
            component_voltage = node_voltages[component["node1"]] - node_voltages[component["node2"]]
            current = component_voltage / component["value"]
            component_results[component["id"]] = {
                "current": current,
                "voltage": component_voltage,
                "power": component_voltage * current,
            }

        source_results = []
        for group_index, group in enumerate(source_groups):
            representative = group[0]
            group_current = values[source_indices[representative["id"]]]
            voltage = node_voltages[representative["node1"]] - node_voltages[representative["node2"]]
            for battery in group:
                source_current = group_current / len(group)
                source_result = {
                    # Passive sign convention: positive current enters terminal 1.
                    # Identical ideal parallel sources use an explicit equal-share assumption.
                    "current": source_current,
                    "voltage": voltage,
                    "power": voltage * source_current,
                }
                component_results[battery["id"]] = source_result
                source_results.append({"id": battery["id"], **source_result,
                                       "supplied_current": -source_current,
                                       "supplied_power": -source_result["power"],
                                       "group_id": group_index + 1,
                                       "group_supplied_current": -group_current,
                                       "sharing_assumption": "equal" if len(group) > 1 else None})

        primary_source = source_results[0]
        # Keep the legacy total-current metric as the net current of the first
        # source group. Derive load equivalent resistance from dissipated power
        # and current only when all independent source groups carry the same
        # current magnitude (the normal case for series-connected sources).
        total_current = -values[source_indices[source_groups[0][0]["id"]]]
        voltage = primary_source["voltage"]
        load_power = sum(component_results[item["id"]]["power"] for item in resistors)
        if load_power <= 1e-12:
            raise ValueError("The sources do not deliver power to a resistor or bulb; check source polarities and connections.")
        group_currents = [-values[source_indices[group[0]["id"]]] for group in source_groups]
        reference_current = abs(group_currents[0])
        currents_match = all(abs(abs(current) - reference_current) <= 1e-7 * max(1.0, reference_current)
                             for current in group_currents[1:])
        equivalent_resistance = load_power / (reference_current ** 2) if currents_match and reference_current > 1e-12 else None

        return {
            "voltage": voltage,
            "equivalent_resistance": equivalent_resistance,
            "total_current": total_current,
            "primary_source_id": primary_source["id"],
            "sources": source_results,
            "source_group_count": len(source_groups),
            "components": component_results,
        }
