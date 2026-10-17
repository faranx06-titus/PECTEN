from app.physics.circuit_graph import CircuitGraph


graph = CircuitGraph()


graph.add_component(
    "B1",
    "battery",
    12,
    "N1",
    "N0"
)

graph.add_component(
    "R1",
    "resistor",
    2,
    "N1",
    "N2"
)

graph.add_component(
    "R2",
    "resistor",
    6,
    "N2",
    "N0"
)

graph.add_component(
    "R3",
    "resistor",
    3,
    "N2",
    "N0"
)


graph.print_graph()