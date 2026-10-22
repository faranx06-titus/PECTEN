# Circuit data schema

Both `/analyze-circuit` and `/simulate-circuit` use the nested shape returned by the vision model. The simulation request wraps that object as `{ "circuit": <object> }` (the wrapper key contains the full vision-shaped data, including its nested `circuit`).

```json
{
  "problem": { "text": "Find the total current", "asked_quantity": "current" },
  "circuit": {
    "type": "series | parallel | mixed | single_loop | unknown",
    "components": [
      { "id": "B1", "type": "battery", "value": 12, "unit": "V", "terminals": ["1", "2"], "visual": { "terminal_points": { "1": [30, 80], "2": [30, 140] } } },
      { "id": "R1", "type": "resistor", "value": 4, "unit": "ohm", "terminals": ["1", "2"] }
    ],
    "connections": [
      { "from": { "component": "B1", "terminal": "1" }, "to": { "component": "R1", "terminal": "1" } },
      { "from": { "component": "R1", "terminal": "2" }, "to": { "component": "B1", "terminal": "2" } }
    ],
    "nodes": [
      { "id": "N1", "terminals": [
        { "component": "B1", "terminal": "1" },
        { "component": "R1", "terminal": "1" }
      ] }
    ]
  },
  "visual": { "image_width": 700, "image_height": 400, "wire_paths": [] }
}
```

## Fields

- Every component has a unique `id`, a supported `type`, and exactly two terminal labels. The electrical solver currently supports `resistor`, `bulb`, `battery`, `cell`, and `wire`; vision may recognize additional symbols, but they cannot be solved until implemented.
- `resistor` and `bulb` values are resistance in ohms and must be positive numbers.
- `battery` and `cell` values are voltage magnitude in volts and must be positive numbers. If `polarity` is supplied, `terminal_1`/`terminal_2` can identify `positive`/`negative` (or `+`/`-`); absent polarity, terminal 1 is treated as positive and terminal 2 as negative. A cell is normalized to a battery by the graph builder.
- `wire` components are ideal terminal joins. They do not have a numeric value.
- Every connection endpoint must reference an existing component and one of its terminal labels.
- When `circuit.nodes` is present, it is the electrical-topology source of truth. Each terminal must appear in exactly one node group; terminals grouped together are electrically connected. `connections` remains supported for older payloads.
- `visual.wire_paths` is a list of visible wire paths. Each path has `from_component`, `from_terminal`, `to_component`, `to_terminal`, and ordered `[x, y]` points in the analyzed raster image's pixel coordinates. A path must join endpoints on the same electrical node to receive a solved animation current.
- `component.visual.terminal_points` optionally maps terminal labels to image pixel coordinates. The review overlay uses these points to label the proposed electrical nodes on the source image.
- Top-level `review_items` optionally lists uncertain visual detections. A `connection` item identifies two endpoints; a `component` item identifies a component ID and suggested type. Items include qualitative `confidence` (`low` or `medium`) and a short `reason`. This is a model-reported review cue, not a calibrated probability or proof that other detections are correct. `problem` may contain extracted `text` and a concise `asked_quantity` such as `current`, `voltage`, `resistance`, `power`, or `brightness`.

The current solver requires one or more batteries/cells and a connected network with at least one resistor or bulb. It handles series, parallel, mixed series-parallel, and connected bridge networks using MNA. Each component result includes signed `current`, signed `voltage` (terminal 1 to terminal 2 after polarity normalization), and signed `power` (positive means absorbed under passive sign convention); source results also include `supplied_current` and `supplied_power` with the opposite sign. `total_current` is the supplied current of the first independent source group. Equivalent load resistance is returned only when source groups carry the same current magnitude. Identical ideal sources directly in parallel use an equal-current-sharing assumption. Different ideal voltage sources in parallel are rejected; accurate real source sharing requires internal resistance. Unknown resistor/bulb values cannot be simulated. Validation or unsupported-topology details use HTTP 422 on `/simulate-circuit`; successful image extraction with an unsolved candidate returns `simulation_error` so the UI can offer topology correction.

Successful simulation results include `components`, `sources`, `wire_currents`, `kcl_check`, `physics_checks` (Kirchhoff current law, Ohm's law, and power balance), and `topology_check` (disconnected sections and possible open ends). `wire_currents` records `{current, resolved}` for each traced path; unresolved paths are not animated. The selected spanning-tree flow through ideal wire networks is one KCL-consistent visual routing, not a unique physical solution. Failed physics checks prevent animation. Image analysis returns a candidate topology: equation checks verify internal consistency, not that the connections match the source image. The interface exposes inferred endpoint groups and lets the user regroup terminals; analyzed-view animation stays disabled until the learner confirms the topology. An unsolvable candidate is retained for correction rather than discarded.

The frontend recomputes after source-voltage or resistor/bulb-resistance edits through `/simulate-circuit`. Dash speed, thickness, and spacing are visual mappings of solved current magnitude, not literal charge-carrier drift speed. Bulb glow follows solved electrical power qualitatively and is not a calibrated brightness or thermal model. Bulbs use fixed resistance in the electrical solver.

## Extraction benchmark

`backend/tools/circuit_benchmark.py` generates a small gold set of series and parallel circuit images and scores model predictions independently of solver results. See the script usage for `generate` and `score` commands. The connection F1 uses pairs of terminals that the prediction places on the same electrical node; it does not evaluate visual localization, values, or solver correctness.
