def calculate_current(voltage, resistance):
    """Ohm's law: I = V / R."""

    if resistance <= 0:
        raise ValueError("Resistance must be greater than zero.")

    return voltage / resistance


def calculate_series_resistance(resistors):
    """Equivalent resistance of resistors in series."""

    if not resistors:
        raise ValueError("No resistors provided.")

    total = 0

    for resistor in resistors:
        resistance = resistor["value"]

        if resistance is None or resistance <= 0:
            raise ValueError(
                f"Invalid resistance for {resistor['id']}."
            )

        total += resistance

    return total


def calculate_parallel_resistance(resistors):
    """Equivalent resistance of resistors in parallel."""

    if not resistors:
        raise ValueError("No resistors provided.")

    inverse_total = 0

    for resistor in resistors:
        resistance = resistor["value"]

        if resistance is None or resistance <= 0:
            raise ValueError(
                f"Invalid resistance for {resistor['id']}."
            )

        inverse_total += 1 / resistance

    return 1 / inverse_total


def detect_topology(circuit_data):
    """
    Detect basic circuit topology.

    Supports:
    - single resistor
    - series
    - parallel
    - mixed
    """

    components = circuit_data["circuit"]["components"]

    resistors = [
        component
        for component in components
        if component["type"] == "resistor"
    ]

    if len(resistors) == 0:
        raise ValueError("No resistors found.")

    if len(resistors) == 1:
        return "single_resistor"

    connections = circuit_data["circuit"]["connections"]

    # Count how many connections touch each component.
    connection_count = {
        resistor["id"]: 0
        for resistor in resistors
    }

    for connection in connections:

        from_id = connection["from"]["component"]
        to_id = connection["to"]["component"]

        if from_id in connection_count:
            connection_count[from_id] += 1

        if to_id in connection_count:
            connection_count[to_id] += 1

    # In a simple series circuit, the internal resistor
    # generally has two connections.
    #
    # If the topology contains branching, classify it
    # as mixed unless every resistor has the same endpoints.

    neighbour_map = {
        resistor["id"]: set()
        for resistor in resistors
    }

    for connection in connections:

        from_id = connection["from"]["component"]
        to_id = connection["to"]["component"]

        if from_id in neighbour_map:
            neighbour_map[from_id].add(to_id)

        if to_id in neighbour_map:
            neighbour_map[to_id].add(from_id)

    neighbour_sets = list(neighbour_map.values())

    # Simple parallel:
    # all resistors have identical neighbours.
    if len(neighbour_sets) > 1:

        first = neighbour_sets[0]

        if all(
            neighbours == first
            for neighbours in neighbour_sets
        ):
            return "parallel"

    # Simple series if there are no branching nodes.
    max_connections = max(connection_count.values())

    if max_connections <= 2:
        return "series"

    return "mixed"


def solve_simple_circuit(circuit_data):
    """
    Solve single, series, or parallel circuit.
    """

    components = circuit_data["circuit"]["components"]

    battery = None
    resistors = []

    for component in components:

        if component["type"] == "battery":
            battery = component

        elif component["type"] == "resistor":
            resistors.append(component)

    if battery is None:
        raise ValueError("No battery found.")

    if not resistors:
        raise ValueError("No resistors found.")

    voltage = battery["value"]

    if voltage is None or voltage <= 0:
        raise ValueError("Invalid battery voltage.")

    topology = detect_topology(circuit_data)

    if topology == "single_resistor":

        resistor = resistors[0]

        resistance = resistor["value"]

        total_resistance = resistance
        total_current = calculate_current(
            voltage,
            total_resistance
        )

        resistor_results = [
            {
                "id": resistor["id"],
                "resistance": resistance,
                "voltage": voltage,
                "current": total_current,
                "power": voltage * total_current
            }
        ]

    elif topology == "series":

        total_resistance = calculate_series_resistance(
            resistors
        )

        total_current = calculate_current(
            voltage,
            total_resistance
        )

        resistor_results = []

        for resistor in resistors:

            resistance = resistor["value"]

            voltage_drop = (
                total_current * resistance
            )

            resistor_results.append(
                {
                    "id": resistor["id"],
                    "resistance": resistance,
                    "voltage": voltage_drop,
                    "current": total_current,
                    "power": voltage_drop * total_current
                }
            )

    elif topology == "parallel":

        total_resistance = calculate_parallel_resistance(
            resistors
        )

        total_current = calculate_current(
            voltage,
            total_resistance
        )

        resistor_results = []

        for resistor in resistors:

            resistance = resistor["value"]

            branch_current = calculate_current(
                voltage,
                resistance
            )

            resistor_results.append(
                {
                    "id": resistor["id"],
                    "resistance": resistance,
                    "voltage": voltage,
                    "current": branch_current,
                    "power": voltage * branch_current
                }
            )

    else:
        raise ValueError(
            "Mixed circuit requires the mixed-circuit solver."
        )

    total_power = sum(
        component["power"]
        for component in resistor_results
    )

    return {
        "circuit_type": topology,
        "total_resistance": total_resistance,
        "total_current": total_current,
        "total_power": total_power,
        "unit": {
            "resistance": "Ω",
            "voltage": "V",
            "current": "A",
            "power": "W"
        },
        "components": resistor_results
    }


def solve_mixed_circuit(circuit_data):
    """
    Solve:

        R1 in series with (R2 || R3)

    This is our first mixed topology.
    """

    components = circuit_data["circuit"]["components"]

    battery = next(
        (
            component
            for component in components
            if component["type"] == "battery"
        ),
        None
    )

    resistors = [
        component
        for component in components
        if component["type"] == "resistor"
    ]

    if battery is None:
        raise ValueError("No battery found.")

    if len(resistors) != 3:
        raise ValueError(
            "This mixed solver currently expects exactly 3 resistors."
        )

    voltage = battery["value"]

    r1 = next(r for r in resistors if r["id"] == "R1")
    r2 = next(r for r in resistors if r["id"] == "R2")
    r3 = next(r for r in resistors if r["id"] == "R3")

    R1 = r1["value"]
    R2 = r2["value"]
    R3 = r3["value"]

    # R2 and R3 are parallel.
    parallel_resistance = (
        1 / ((1 / R2) + (1 / R3))
    )

    # R1 is in series with the parallel combination.
    total_resistance = R1 + parallel_resistance

    # Total circuit current.
    total_current = calculate_current(
        voltage,
        total_resistance
    )

    # Voltage across R1.
    voltage_R1 = total_current * R1

    # Voltage across the parallel section.
    parallel_voltage = voltage - voltage_R1

    # Branch currents.
    current_R2 = calculate_current(
        parallel_voltage,
        R2
    )

    current_R3 = calculate_current(
        parallel_voltage,
        R3
    )

    resistor_results = [
        {
            "id": "R1",
            "resistance": R1,
            "voltage": voltage_R1,
            "current": total_current,
            "power": voltage_R1 * total_current
        },
        {
            "id": "R2",
            "resistance": R2,
            "voltage": parallel_voltage,
            "current": current_R2,
            "power": parallel_voltage * current_R2
        },
        {
            "id": "R3",
            "resistance": R3,
            "voltage": parallel_voltage,
            "current": current_R3,
            "power": parallel_voltage * current_R3
        }
    ]

    total_power = sum(
        component["power"]
        for component in resistor_results
    )

    return {
        "circuit_type": "mixed",
        "total_resistance": total_resistance,
        "total_current": total_current,
        "total_power": total_power,
        "unit": {
            "resistance": "Ω",
            "voltage": "V",
            "current": "A",
            "power": "W"
        },
        "components": resistor_results
    }


def solve_circuit(circuit_data):
    """Main circuit solver."""

    topology = detect_topology(circuit_data)

    if topology == "mixed":
        return solve_mixed_circuit(circuit_data)

    return solve_simple_circuit(circuit_data)