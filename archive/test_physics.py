from app.physics.current_electricity import calculate_current

voltage = 12
resistance = 4

current = calculate_current(voltage, resistance)

print(f"Voltage: {voltage} V")
print(f"Resistance: {resistance} Ω")
print(f"Current: {current} A")