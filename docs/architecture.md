# Architecture

## Current end-to-end flow

1. `UploadQuestion` previews raster images or renders a selected PDF page in the browser with PDF.js. A learner can crop the page and paste a question. The selected image region and question go as multipart form data to `POST /analyze-circuit`. A user Gemini key is sent in `X-API-Key`; otherwise the server uses `GEMINI_API_KEY`.
2. `backend/app/ai/vision.py` asks Gemini for JSON describing the problem, component types/values, terminals, node groups, visual coordinates, and traced wires. The model is explicitly instructed to extract rather than solve.
3. `backend/app/services/analyzer.py` validates the candidate, builds a `CircuitGraph`, checks topology, solves the graph with MNA, then checks KCL, branch Ohm's law, and power balance.
4. The API returns candidate vision data, graph diagnostics, reduction history, and the numerical solution. If image extraction succeeds but the candidate graph cannot be solved, the response retains the candidate with a `simulation_error` for learner correction.
5. React displays the original page beside the analyzed image overlay. Learners inspect inferred terminal groups, repair connections, confirm the topology, and edit component values. Edits go to `POST /simulate-circuit`, which uses the same local deterministic solve pipeline.

## Backend responsibilities

- `ai/vision.py`: Gemini client setup, image prompt, model fallback, JSON decoding.
- `validation/circuit_validator.py`: structural checks and positive values for resistors, bulbs, and cells/batteries.
- `physics/graph_builder.py`: terminal-level disjoint-set merging; explicit wire components are ideal terminal joins, and `cell` is normalized to `battery`.
- `physics/circuit_reducer.py`: repeatedly replaces parallel and series resistor/bulb groups with equivalent resistors.
- `physics/circuit_solver.py`: uses modified nodal analysis for one or more ideal batteries/cells and connected resistor/bulb networks, including bridges. Identical ideal sources directly in parallel use an explicit equal-sharing assumption; incompatible ideal parallel voltages/polarities are rejected because source internal resistances are not modeled.
- `services/analyzer.py`: reports suspicious open ends and blocks results that fail the numerical physics checks.
- `physics/solution_trace.py`: recovers current, voltage, and power for original resistive components.

## Frontend responsibilities

- `App.jsx`: page state and coordination between upload and analysis views.
- `services/api.js`: HTTP calls and surfaced API errors; `VITE_API_URL` configures the backend origin.
- `AnalyzedCircuitSimulator.jsx`: topology review/editor, live value controls, numerical readings, and current/power overlay on the analyzed image.
- `GeneratedCircuit.jsx`: generated circuit view and component results. The app disables this view for multiple sources because its diagram currently renders one source.

## Supported physics and limitations

The solver supports connected series, parallel, mixed series-parallel, and resistor bridge networks with one or more ideal voltage sources and known resistor/bulb values. It computes node voltages, component currents, voltages, and powers. KCL residuals, branch Ohm's-law residuals, and total power balance are checked before animation. The analyzed view animates only after the learner confirms the topology and numerical checks pass. Wire animation routes solved current through traced wire paths using a deterministic spanning tree; ideal junctions have zero resistance, so their internal current distribution is not unique. Current dash pace and thickness are visual encodings derived from solved amperes; they are not physical electron-drift speeds. Bulbs remain distinct in the UI, but the solver treats them as fixed resistances. Glow follows calculated electrical power qualitatively; it is not calibrated brightness and does not model filament temperature or transient warm-up. Identical parallel sources use equal sharing as a symmetry assumption; unequal real source sharing requires internal resistance. Missing/invalid values and malformed/disconnected graphs are rejected or returned for topology correction. The series/parallel reducer is retained for explanation history and does not determine the numerical result. This is a learning prototype, not an engineering-grade simulator.

Image interpretation uses Gemini, but recalculating or editing component values uses the local physics pipeline and does not consume Gemini API calls. Voltage or resistance edits therefore change the solved node voltages, branch currents, and power, and the UI updates its readings/visual cues from the new solution. A mathematically valid solution is only as accurate as the extracted values and terminal connections. Numerical checks verify internal consistency; they do not prove that the candidate graph matches the image. Learners can inspect the inferred terminal groups and edit them before confirming.

PDF page selection, manual cropping, original-page reference, and image overlays are supported in the browser. The backend receives a raster image, not a PDF document. Whole-document text extraction, automatic question-region detection, and mapping coordinates back to PDF units remain future work. The unused parser/reasoning/simulation framework placeholders were removed; the active analysis pipeline is documented above.

## Current visual behavior

- Branch colors identify separate resistor/bulb paths; wire colors are associated with adjacent branches where possible.
- Animated dashes move in the solved conventional-current direction. The visual pace, spacing, and thickness use current magnitude as a readable cue, not a literal microscopic transport model.
- Resistor/bulb controls display the entered resistance and solved current, voltage, and power. Source controls display voltage and solved current/power.
- Bulb glow and the light-output indicator respond to nonnegative solved power on a qualitative scale. A zero-power bulb is shown unlit. There is no wattage rating or validated brightness calibration.

## Extension direction

To add another technical domain, introduce a domain-specific extraction schema and validator, a solver behind the shared service layer, and an overlay/editor that retains source-image coordinates. For more realistic cells and lamps, add explicit internal resistance and component models with known parameters. Keep model extraction separate from deterministic calculation so a vision model does not invent numerical answers.
