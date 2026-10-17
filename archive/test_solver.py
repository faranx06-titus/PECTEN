import json

from app.physics.graph_builder import build_circuit_graph
from app.physics.circuit_reducer import CircuitReducer
from app.physics.circuit_solver import CircuitSolver


JSON_PATH = "samples/current_electricity/mixed_test.json"


with open(JSON_PATH, "r", encoding="utf-8") as file:
    circuit_data = json.load(file)


graph = build_circuit_graph(circuit_data)

reducer = CircuitReducer(graph)

print("===== REDUCING CIRCUIT =====")

reducer.reduce_all()
reducer.print_reduction_history()


solver = CircuitSolver(graph)

result = solver.solve_total_current()


print("\n===== SOLUTION =====")

print(f"Voltage: {result['voltage']} V")
print(
    f"Equivalent resistance: "
    f"{result['equivalent_resistance']} Ω"
)
print(
    f"Total current: "
    f"{result['total_current']} A"
)