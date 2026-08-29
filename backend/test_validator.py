import json

from app.validation.circuit_validator import validate_circuit


JSON_PATH = "samples/current_electricity/test_circuit.json"


with open(JSON_PATH, "r", encoding="utf-8") as file:
    circuit_data = json.load(file)


print("Validating saved circuit...")

errors = validate_circuit(circuit_data)

if errors:
    print("\n❌ CIRCUIT INVALID")

    for error in errors:
        print("-", error)

else:
    print("\n✅ CIRCUIT VALID")