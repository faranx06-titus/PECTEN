"""Check known series, parallel, mixed, and bridge DC resistor networks.

Run from the backend directory with: py tools/physics_benchmark.py
This measures the deterministic physics solver only; it does not evaluate
Gemini image recognition or circuit-overlay coordinates.
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.analyzer import solve_circuit_data


def _endpoint(component, terminal):
    return {"component": component, "terminal": str(terminal)}


def _circuit(component_specs, node_specs):
    components = []
    nodes = []
    for component_id, kind, value in component_specs:
        components.append({
            "id": component_id,
            "type": kind,
            "value": value,
            "terminals": ["1", "2"],
        })
    for index, members in enumerate(node_specs, 1):
        nodes.append({"id": f"N{index}", "terminals": [_endpoint(*item) for item in members]})
    return {"circuit": {"components": components, "nodes": nodes}}


CASES = [
    {
        "id": "series",
        "data": _circuit(
            [("B1", "battery", 9), ("R1", "resistor", 100), ("R2", "resistor", 200)],
            [[("B1", 1), ("R1", 1)], [("R1", 2), ("R2", 1)], [("R2", 2), ("B1", 2)]],
        ),
        "expected_current": {"B1": 0.03, "R1": 0.03, "R2": 0.03},
        "expected_equivalent_resistance": 300,
    },
    {
        "id": "parallel",
        "data": _circuit(
            [("B1", "battery", 9), ("R1", "resistor", 100), ("R2", "bulb", 200)],
            [[("B1", 1), ("R1", 1), ("R2", 1)], [("B1", 2), ("R1", 2), ("R2", 2)]],
        ),
        "expected_current": {"B1": 0.135, "R1": 0.09, "R2": 0.045},
        "expected_equivalent_resistance": 200 / 3,
    },
    {
        "id": "mixed_series_parallel",
        "data": _circuit(
            [("B1", "battery", 12), ("R1", "resistor", 100), ("R2", "resistor", 200), ("R3", "resistor", 300)],
            [[("B1", 1), ("R1", 1)], [("R1", 2), ("R2", 1), ("R3", 1)], [("R2", 2), ("R3", 2), ("B1", 2)]],
        ),
        "expected_current": {"B1": 12 / 220, "R1": 12 / 220, "R2": 6.545454545454546 / 200, "R3": 6.545454545454546 / 300},
        "expected_equivalent_resistance": 220,
    },
    {
        "id": "balanced_bridge",
        "data": _circuit(
            [("B1", "battery", 12), ("R1", "resistor", 100), ("R2", "resistor", 100),
             ("R3", "resistor", 200), ("R4", "resistor", 200), ("R5", "resistor", 100)],
            [[("B1", 1), ("R1", 1), ("R3", 1)],
             [("R1", 2), ("R2", 1), ("R5", 1)],
             [("R3", 2), ("R4", 1), ("R5", 2)],
             [("B1", 2), ("R2", 2), ("R4", 2)]],
        ),
        "expected_current": {"B1": 0.12, "R1": 0.06, "R2": 0.06, "R3": 0.06, "R4": 0.06, "R5": 0.0},
        "expected_equivalent_resistance": 100,
    },
]


def run():
    results = []
    for case in CASES:
        try:
            _, _, solution = solve_circuit_data(case["data"])
            component_errors = {
                component_id: abs(abs(solution["components"][component_id]["current"]) - expected)
                for component_id, expected in case["expected_current"].items()
            }
            equivalent_error = abs(solution["equivalent_resistance"] - case["expected_equivalent_resistance"])
            passed = (
                all(math.isclose(abs(solution["components"][component_id]["current"]), expected,
                                 rel_tol=1e-7, abs_tol=1e-9)
                    for component_id, expected in case["expected_current"].items())
                and math.isclose(solution["equivalent_resistance"], case["expected_equivalent_resistance"],
                                 rel_tol=1e-7, abs_tol=1e-9)
                and solution["physics_checks"]["passed"]
            )
            results.append({
                "case": case["id"], "passed": passed,
                "max_component_current_error_a": max(component_errors.values(), default=0),
                "equivalent_resistance_error_ohm": equivalent_error,
                "physics_checks": solution["physics_checks"],
            })
        except Exception as error:
            results.append({"case": case["id"], "passed": False, "error": str(error)})
    report = {"passed": all(result["passed"] for result in results), "cases": results}
    print(json.dumps(report, indent=2))
    return report["passed"]


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)
