import json

from app.physics.graph_builder import build_circuit_graph


JSON_PATH = "samples/current_electricity/mixed_test.json"


with open(JSON_PATH, "r", encoding="utf-8") as file:
    circuit_data = json.load(file)


graph = build_circuit_graph(circuit_data)

graph.print_graph()