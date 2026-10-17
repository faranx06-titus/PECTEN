import json

from app.ai.vision import analyze_circuit
from app.physics.current_electricity import solve_circuit


IMAGE_PATH = "samples/current_electricity/test_circuit.png"


print("Analyzing circuit with Gemini...")

raw_result = analyze_circuit(IMAGE_PATH)

# Gemini returns JSON as text.
circuit_data = json.loads(raw_result)

print("\n===== CIRCUIT UNDERSTANDING =====")
print(json.dumps(circuit_data, indent=2))

print("\nSolving with PECTEN Physics Engine...")

result = solve_circuit(circuit_data)

print("\n===== PHYSICS RESULT =====")
print(f"{result['quantity']}: {result['value']} {result['unit']}")