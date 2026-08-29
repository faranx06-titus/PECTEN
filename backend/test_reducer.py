import json

from app.physics.graph_builder import build_circuit_graph
from app.physics.circuit_reducer import CircuitReducer


JSON_PATH = "samples/current_electricity/mixed_test.json"


with open(JSON_PATH, "r", encoding="utf-8") as file:
    circuit_data = json.load(file)


graph = build_circuit_graph(circuit_data)

reducer = CircuitReducer(graph)


print("===== ORIGINAL GRAPH =====")

graph.print_graph()


# -------------------------------
# Step 1: Parallel reduction
# -------------------------------

parallel_groups = reducer.find_parallel_groups()

print("\n===== PARALLEL GROUPS =====")

for group in parallel_groups:
    print(group)


if parallel_groups:

    equivalent_id = reducer.reduce_parallel_group(
        parallel_groups[0]
    )

    equivalent = graph.get_component(
        equivalent_id
    )

    print("\nParallel reduction:")
    print(
        f"{equivalent_id} = "
        f"{equivalent['value']} Ω"
    )


# -------------------------------
# Step 2: Series reduction
# -------------------------------

series_groups = reducer.find_series_groups()

print("\n===== SERIES GROUPS =====")

for group in series_groups:
    print(group)


if series_groups:

    equivalent_id = reducer.reduce_series_group(
        series_groups[0]
    )

    equivalent = graph.get_component(
        equivalent_id
    )

    print("\nSeries reduction:")
    print(
        f"{equivalent_id} = "
        f"{equivalent['value']} Ω"
    )


print("\n===== FINAL GRAPH =====")

graph.print_graph()