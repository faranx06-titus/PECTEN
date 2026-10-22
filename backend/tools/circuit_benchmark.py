"""Generate tiny gold circuit diagrams and score extracted topology predictions.

Usage:
  python -m tools.circuit_benchmark generate /path/to/corpus
  python -m tools.circuit_benchmark score /path/to/corpus predictions.jsonl

Prediction JSONL rows contain {"id": "series_2", "vision": { ... }} or the
vision-shaped object directly. Metrics are intentionally split: component
recognition and terminal-pair connectivity do not measure solver accuracy.
"""

import argparse
import itertools
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CANVAS = (520, 360)
INK = (25, 37, 55)


def _font(size=15):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _resistor(draw, start, end, label, value):
    x1, y1 = start
    x2, y2 = end
    if y1 == y2:
        left, right = sorted((x1, x2))
        draw.line((left, y1, left + 24, y1), fill=INK, width=3)
        draw.rectangle((left + 24, y1 - 12, right - 24, y1 + 12), outline=INK, width=3)
        draw.line((right - 24, y1, right, y1), fill=INK, width=3)
        cx, cy = (left + right) / 2, y1
    else:
        top, bottom = sorted((y1, y2))
        draw.line((x1, top, x1, top + 20), fill=INK, width=3)
        draw.rectangle((x1 - 12, top + 20, x1 + 12, bottom - 20), outline=INK, width=3)
        draw.line((x1, bottom - 20, x1, bottom), fill=INK, width=3)
        cx, cy = x1 + 34, (top + bottom) / 2
    draw.text((cx - 15, cy - 31), f"{label} {value}Ω", fill=INK, font=_font(13))


def _battery(draw, positive, negative):
    x = positive[0]
    draw.line((x, positive[1], x, positive[1] + 23), fill=INK, width=3)
    draw.line((x - 12, positive[1] + 23, x + 12, positive[1] + 23), fill=INK, width=4)
    draw.line((x - 19, positive[1] + 35, x + 19, positive[1] + 35), fill=INK, width=2)
    draw.line((x, positive[1] + 35, x, negative[1]), fill=INK, width=3)
    draw.text((x + 22, positive[1] + 15), "+", fill=INK, font=_font(15))
    draw.text((x + 22, positive[1] + 35), "−", fill=INK, font=_font(15))
    draw.text((x - 15, positive[1] - 25), "B1 9V", fill=INK, font=_font(13))


def _draw_case(case, path):
    image = Image.new("RGB", CANVAS, "white")
    draw = ImageDraw.Draw(image)
    if case == "series_2":
        points = {"bp": (90, 90), "bn": (90, 290), "r1a": (190, 90), "r1b": (300, 90),
                  "r2a": (410, 90), "r2b": (410, 290)}
        wires = [[points["bp"], points["r1a"]], [points["r1b"], (410, 90)],
                 [points["r2b"], (250, 290), points["bn"]]]
        # R2 is vertical; R1 and R2 form a single loop with an explicit return path.
        nodes = [[("B1", "1"), ("R1", "1")], [("R1", "2"), ("R2", "1")],
                 [("R2", "2"), ("B1", "2")]]
        components = [{"id": "B1", "type": "battery", "value": 9, "terminals": ["1", "2"],
                       "visual": {"terminal_points": {"1": list(points["bp"]), "2": list(points["bn"])}}},
                      {"id": "R1", "type": "resistor", "value": 100, "terminals": ["1", "2"]},
                      {"id": "R2", "type": "resistor", "value": 200, "terminals": ["1", "2"]}]
        _battery(draw, points["bp"], points["bn"])
        _resistor(draw, points["r1a"], points["r1b"], "R1", 100)
        _resistor(draw, points["r2a"], points["r2b"], "R2", 200)
        draw.line((points["r2b"], points["bn"]), fill=INK, width=3)
        draw.line((points["r1b"], points["r2a"]), fill=INK, width=3)
        wires = [[points["bp"], points["r1a"]], [points["r1b"], points["r2a"]],
                 [points["r2b"], points["bn"]]]
    elif case == "parallel_2":
        points = {"bp": (90, 105), "bn": (90, 255), "a1": (210, 105), "b1": (370, 105),
                  "a2": (210, 255), "b2": (370, 255)}
        nodes = [[("B1", "1"), ("R1", "1"), ("R2", "1")],
                 [("B1", "2"), ("R1", "2"), ("R2", "2")]]
        components = [{"id": "B1", "type": "battery", "value": 9, "terminals": ["1", "2"]},
                      {"id": "R1", "type": "resistor", "value": 100, "terminals": ["1", "2"]},
                      {"id": "R2", "type": "resistor", "value": 220, "terminals": ["1", "2"]}]
        _battery(draw, points["bp"], points["bn"])
        _resistor(draw, points["a1"], points["b1"], "R1", 100)
        _resistor(draw, points["a2"], points["b2"], "R2", 220)
        wires = [[points["bp"], (150, 105), points["a1"]], [(150, 105), (150, 255), points["a2"]],
                 [points["b1"], (440, 105), (440, 255), points["b2"]],
                 [(440, 255), (440, 255), points["bn"]]]
        draw.line((points["bp"], (150, 105), points["a1"]), fill=INK, width=3)
        draw.line((150, 105, 150, 255, points["a2"]), fill=INK, width=3)
        draw.line((points["b1"], (440, 105), (440, 255), points["b2"]), fill=INK, width=3)
        draw.line((points["b2"], points["bn"]), fill=INK, width=3)
    else:
        raise ValueError(f"Unknown benchmark case: {case}")

    image.save(path)
    circuit_nodes = [{"id": f"N{index + 1}", "terminals": [
        {"component": comp, "terminal": terminal} for comp, terminal in group
    ]} for index, group in enumerate(nodes)]
    return {"id": case, "circuit": {"type": case, "components": components,
                                     "connections": [], "nodes": circuit_nodes}}


def generate(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    for case in ("series_2", "parallel_2"):
        truth = _draw_case(case, output_dir / f"{case}.png")
        (output_dir / f"{case}.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    print(f"Generated 2 gold circuit images in {output_dir}")


def _terminal_partition(circuit):
    terminals = {(component.get("id"), terminal)
                 for component in circuit.get("components", [])
                 for terminal in component.get("terminals", [])}
    groups = circuit.get("nodes") or []
    if groups:
        return [{(endpoint.get("component"), endpoint.get("terminal"))
                 for endpoint in group.get("terminals", [])} for group in groups]
    parent = {item: item for item in terminals}
    def find(item):
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item
    for edge in circuit.get("connections", []):
        left = (edge.get("from", {}).get("component"), edge.get("from", {}).get("terminal"))
        right = (edge.get("to", {}).get("component"), edge.get("to", {}).get("terminal"))
        if left in parent and right in parent:
            parent[find(right)] = find(left)
    groups_by_root = {}
    for item in terminals:
        groups_by_root.setdefault(find(item), set()).add(item)
    return list(groups_by_root.values())


def _same_node_pairs(partition):
    return {tuple(sorted((left, right))) for group in partition for left, right in itertools.combinations(group, 2)}


def score(truth_dir, predictions_path):
    truths = {path.stem: json.loads(path.read_text(encoding="utf-8"))
              for path in truth_dir.glob("*.json")}
    predictions = {}
    for line in predictions_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            predictions[row["id"]] = row.get("vision", row)
    component_tp = component_fp = component_fn = 0
    expected_value_count = correct_value_count = 0
    tp = fp = fn = 0
    for case_id, truth in truths.items():
        if case_id not in predictions:
            print(f"Missing prediction: {case_id}")
            continue
        expected = truth["circuit"]
        predicted = predictions[case_id].get("circuit", {})
        expected_components = {(item["id"], item["type"]) for item in expected.get("components", [])}
        predicted_components = {(item.get("id"), item.get("type")) for item in predicted.get("components", [])}
        predicted_by_id = {item.get("id"): item for item in predicted.get("components", []) if item.get("id")}
        component_tp += len(expected_components & predicted_components)
        component_fp += len(predicted_components - expected_components)
        component_fn += len(expected_components - predicted_components)
        for item in expected.get("components", []):
            expected_value = item.get("value")
            if not isinstance(expected_value, (int, float)):
                continue
            expected_value_count += 1
            guess = predicted_by_id.get(item["id"], {})
            actual_value = guess.get("value")
            if (guess.get("type") == item.get("type")
                    and isinstance(actual_value, (int, float))
                    and math.isclose(actual_value, expected_value, rel_tol=0.01, abs_tol=1e-9)):
                correct_value_count += 1
        expected_pairs = _same_node_pairs(_terminal_partition(expected))
        predicted_pairs = _same_node_pairs(_terminal_partition(predicted))
        tp += len(expected_pairs & predicted_pairs)
        fp += len(predicted_pairs - expected_pairs)
        fn += len(expected_pairs - predicted_pairs)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    component_precision = component_tp / (component_tp + component_fp) if component_tp + component_fp else 1.0
    component_recall = component_tp / (component_tp + component_fn) if component_tp + component_fn else 1.0
    component_f1 = 2 * component_precision * component_recall / (component_precision + component_recall) if component_precision + component_recall else 0.0
    print(json.dumps({"component_id_and_type_precision": component_precision,
                      "component_id_and_type_recall": component_recall,
                      "component_id_and_type_f1": component_f1,
                      "numeric_component_value_accuracy_1pct": correct_value_count / expected_value_count if expected_value_count else None,
                      "numeric_component_values_evaluated": expected_value_count,
                      "terminal_pair_connection_precision": precision,
                      "terminal_pair_connection_recall": recall,
                      "terminal_pair_connection_f1": f1,
                      "evaluated_cases": sum(case_id in predictions for case_id in truths)}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("output_dir", type=Path)
    score_parser = subparsers.add_parser("score")
    score_parser.add_argument("truth_dir", type=Path)
    score_parser.add_argument("predictions", type=Path)
    args = parser.parse_args()
    if args.command == "generate":
        generate(args.output_dir)
    else:
        score(args.truth_dir, args.predictions)


if __name__ == "__main__":
    main()
