import json

from app.physics.graph_builder import build_circuit_graph
from app.physics.circuit_reducer import CircuitReducer


JSON_PATH = "samples/current_electricity/mixed_test.json"


with open(JSON_PATH, "r", encoding="utf-8") as file:
    circuit_data = json.load(file)


graph = build_circuit_graph(circuit_data)

print("===== BEFORE REDUCTION =====")
graph.print_graph()


reducer = CircuitReducer(graph)

reducer.reduce_all()


print("\n===== AFTER REDUCTION =====")
graph.print_graph()