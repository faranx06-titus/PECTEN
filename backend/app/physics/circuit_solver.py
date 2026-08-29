
class CircuitSolver:
    def __init__(self, graph):
        self.graph = graph

    def find_battery(self):
        """Find the battery in the circuit."""

        batteries = [
            component
            for component in self.graph.components.values()
            if component["type"] == "battery"
        ]

        if len(batteries) != 1:
            raise ValueError(
                "Currently, the solver requires exactly one battery."
            )

        return batteries[0]

    def find_equivalent_resistor(self):
        """Find the final equivalent resistor."""

        resistors = [
            component
            for component in self.graph.components.values()
            if component["type"] == "resistor"
        ]

        if len(resistors) != 1:
            raise ValueError(
                f"Expected one equivalent resistor, "
                f"found {len(resistors)}."
            )

        return resistors[0]

    def solve_total_current(self):

        battery = self.find_battery()
        resistor = self.find_equivalent_resistor()

        voltage = battery["value"]
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