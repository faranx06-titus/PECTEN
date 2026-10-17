import json

from app.physics.graph_builder import build_circuit_graph
from app.physics.circuit_reducer import CircuitReducer
from app.physics.circuit_solver import CircuitSolver
from app.physics.solution_trace import SolutionTracer


JSON_PATH = "samples/current_electricity/mixed_test.json"


with open(JSON_PATH, "r", encoding="utf-8") as file:
    circuit_data = json.load(file)


# Build graph
graph = build_circuit_graph(circuit_data)


# Reduce
reducer = CircuitReducer(graph)

reducer.reduce_all()


# Solve total current
solver = CircuitSolver(graph)

solution = solver.solve_total_current()

total_current = solution["total_current"]


# Trace backwards
tracer = SolutionTracer(
    graph,
    reducer.reduction_history
)

results = tracer.trace(total_current)


print("\n===== COMPLETE CIRCUIT SOLUTION =====")

for component_id, result in results.items():

    # Don't show temporary equivalent resistors.
    if component_id.startswith("EQ_"):
        continue

    print(
        f"{component_id}: "
        f"I = {result['current']} A | "
        f"V = {result['voltage']} V | "
        f"P = {result['power']} W"
    )