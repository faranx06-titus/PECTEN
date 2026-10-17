import json

from app.validation.circuit_validator import validate_circuit
from app.physics.current_electricity import solve_circuit


JSON_PATH = "samples/current_electricity/test_circuit.json"


with open(JSON_PATH, "r", encoding="utf-8") as file:
    circuit_data = json.load(file)


print("===== PECTEN OFFLINE PIPELINE =====")

print("\n1. Validating circuit...")

errors = validate_circuit(circuit_data)

if errors:
    print("❌ Circuit invalid")

    for error in errors:
        print("-", error)

    raise SystemExit(1)

print("✅ Circuit valid")


print("\n2. Running physics engine...")

result = solve_circuit(circuit_data)


print("\n===== PHYSICS RESULT =====")

print(f"Circuit type: {result['circuit_type']}")
print(f"Total resistance: {result['total_resistance']} Ω")
print(f"Current: {result['current']} {result['unit']}")