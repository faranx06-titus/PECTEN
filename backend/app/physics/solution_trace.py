
class SolutionTracer:

    def __init__(self, graph, reduction_history):

        self.graph = graph
        self.history = reduction_history
        self.results = {}
        self.component_data = {}

        # Save original component information
        for step in self.history:

            for component_id, data in step.get(
                "component_data", {}
            ).items():

                self.component_data[component_id] = data

    def get_component(self, component_id):

        if component_id in self.component_data:
            return self.component_data[component_id]

        return self.graph.get_component(component_id)

    def trace(self, total_current):

        # ==========================================
        # SIMPLE CIRCUIT
        # ==========================================

        if not self.history:

            for component_id, component in self.graph.components.items():

                if component["type"] != "resistor":
                    continue

                resistance = component["value"]

                voltage = total_current * resistance
                power = voltage * total_current

                self.results[component_id] = {
                    "current": total_current,
                    "voltage": voltage,
                    "power": power
                }

            return self.results

        # ==========================================
        # REDUCED CIRCUIT
        # ==========================================

        final_step = self.history[-1]

        self.results[final_step["equivalent"]] = {
            "current": total_current
        }

        # Reverse the reduction process.
        for step in reversed(self.history):

            equivalent_id = step["equivalent"]

            if equivalent_id not in self.results:
                continue

            current = self.results[
                equivalent_id
            ]["current"]

            components = step["components"]

            # ======================================
            # SERIES
            # ======================================

            if step["type"] == "series":

                for component_id in components:

                    component = self.get_component(
                        component_id
                    )

                    resistance = component["value"]

                    voltage = current * resistance
                    power = voltage * current

                    self.results[component_id] = {
                        "current": current,
                        "voltage": voltage,
                        "power": power
                    }

            # ======================================
            # PARALLEL
            # ======================================

            elif step["type"] == "parallel":

                equivalent_resistance = step["resistance"]

                # Same voltage across all
                # parallel branches.
                voltage = (
                    current *
                    equivalent_resistance
                )

                for component_id in components:

                    component = self.get_component(
                        component_id
                    )

                    resistance = component["value"]

                    branch_current = (
                        voltage /
                        resistance
                    )

                    power = (
                        voltage *
                        branch_current
                    )

                    self.results[component_id] = {
                        "current": branch_current,
                        "voltage": voltage,
                        "power": power
                    }

        return self.results

