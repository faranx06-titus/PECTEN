class CircuitSolver:
    def __init__(self, graph):
        self.graph = graph

    def find_batteries(self):
        """Find all batteries in the circuit."""

        batteries = [
            component
            for component in self.graph.components.values()
            if component["type"] == "battery"
        ]

        if not batteries:
            raise ValueError(
                "The circuit must contain at least one battery to have current."
            )

        return batteries

    def find_equivalent_resistor(self):
        """Find the final equivalent resistor."""

        resistors = [
            component
            for component in self.graph.components.values()
            if component["type"] in ["resistor", "bulb"]
        ]

        if len(resistors) != 1:
            raise ValueError(
                f"The circuit could not be fully reduced to a single equivalent resistor. "
                f"It currently has {len(resistors)} resistive elements. "
                f"This may be a complex circuit (like a bridge) that requires Nodal Analysis."
            )

        return resistors[0]

    def solve_total_current(self):
        batteries = self.find_batteries()
        resistor = self.find_equivalent_resistor()

        # For 12th grade physics, we handle the primary battery or
        # the combined voltage of batteries in series.
        voltage = batteries[0]["value"]
        resistance = resistor["value"]

        if resistance <= 0:
            raise ValueError(
                "Equivalent resistance must be greater than zero."
            )

        current = voltage / resistance

        return {
            "voltage": voltage,
            "equivalent_resistance": resistance,
            "total_current": current
        }
