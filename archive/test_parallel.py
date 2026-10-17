import json

from app.physics.current_electricity import solve_circuit


JSON_PATH = "samples/current_electricity/parallel_test.json"


with open(JSON_PATH, "r", encoding="utf-8") as file:
    circuit_data = json.load(file)


result = solve_circuit(circuit_data)


print("===== PARALLEL CIRCUIT TEST =====")

print(f"Circuit type: {result['circuit_type']}")
print(f"Total resistance: {result['total_resistance']} Ω")
print(f"Total current: {result['total_current']} A")
print(f"Total power: {result['total_power']} W")

print("\nCOMPONENT RESULTS:")

for component in result["components"]:
    print(
        f"{component['id']}: "
        f"{component['resistance']} Ω | "
        f"{component['voltage']} V | "
        f"{component['current']} A"
        f"{component['power']} W"
    )