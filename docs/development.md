# Development guide

## Local setup

Follow the backend and frontend setup in the root [README](../README.md). Keep the server Gemini key in `backend/.env`; do not commit `.env` files. The browser uses `VITE_API_URL` for the API origin (defaults to `http://127.0.0.1:8000`). Users can optionally supply a personal Gemini key in Settings; it stays in tab-scoped `sessionStorage` and is sent in the `X-API-Key` header. The server does not persist that key.

## Working on circuit behavior

Use the vision-shaped JSON contract in [circuit-schema.md](circuit-schema.md). Keep it consistent across Gemini output, validation, graph building, and both API endpoints. Put shared solving in `backend/app/services/analyzer.py` so upload and manual edits do not drift into separate implementations.

The numerical solver uses modified nodal analysis on the unmodified graph. It computes each resistor/bulb's voltage, current, and power, plus source readings. The series/parallel reducer runs on a deep copy for explanation history only, so changing reduction behavior should not change calculated values. The same solver is used by image analysis and value edits; edits should never be solved by a separate frontend formula.

When changing animation styles, derive them from solved results and keep the display explicit that motion is illustrative. The current dash mapping responds to absolute solved amperes so source voltage and component resistance edits affect the flow cue even when branch currents scale together. Bulb glow uses solved electrical power as a qualitative visual indicator; it is not a calibrated brightness/temperature model. Show calculated units and do not imply an ideal-wire junction has a unique internal current distribution.

## Working on the UI

The upload editor sends edited circuit data through `simulateCircuit`. Keep user-facing API errors visible, and treat extracted visual coordinates as coordinates in the analyzed raster image. When changing the analysis response, update the circuit schema docs and both `AnalyzedCircuitSimulator` and `GeneratedCircuit`. The generated circuit view currently draws one source; keep it disabled for multiple-source circuits until that renderer is extended.

## Checks

There is no maintained in-repository automated test suite yet. Before relying on a change, manually check the health route, upload with a configured Gemini key, edits to recognized component values, and invalid/unsupported input responses. The `backend/tools` benchmark scripts provide focused manual checks for solver results and image-extraction metrics. Add automated tests as the project stabilizes.

## Known follow-up work

- Add maintained backend and frontend tests around the API contract and calculation pipeline.
- Grow the generated recognition benchmark with manually verified textbook and worksheet scans, including crossings and multiple mixed branches. Report component/type, value, and connection metrics separately.
- Add calibrated confidence scores for image-recognition outputs; the model's current low/medium labels are review hints only.
- Add internal resistance to source models so non-identical parallel cells can be solved without equal-sharing assumptions.
- Add lamp ratings or a validated electrothermal model before describing glow as calibrated brightness.
- Extend the generated circuit view to depict and explain multiple sources before enabling it for those circuits.
- Implement or remove placeholder parser, reasoning, and simulation-framework modules.
