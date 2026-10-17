from app.ai.vision import analyze_circuit

image_path = "samples/current_electricity/test_circuit.png"

result = analyze_circuit(image_path)

print("\n===== PECTEN VISION RESULT =====\n")
print(result)