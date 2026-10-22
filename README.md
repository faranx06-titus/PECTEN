# PECTEN

PECTEN is an AI-assisted current-electricity learning prototype. A learner uploads a circuit image or PDF, selects a PDF page, optionally crops the question and circuit, and can paste the question. The browser renders PDFs and crops them to images. Gemini extracts a candidate circuit; the workspace places calculated current and bulb-power visuals over the analyzed image beside the original page. Learners review connections and edit component values. PECTEN currently handles supported DC resistive circuits, not arbitrary engineering diagrams.

## Current capabilities

- Gemini image analysis returns candidate components, values, terminal coordinates, electrical nodes, visible wire paths, and problem text. PDF page rendering, page selection, and optional cropping happen in the browser; the backend receives a raster image.
- A modified nodal analysis (MNA) solver calculates node voltage and each resistor, bulb, and source current, voltage, and power. It supports series, parallel, mixed, and connected bridge networks.
- The topology review shows inferred connections in plain language. Learners can reconnect or separate terminals and confirm the diagram before current animation starts.
- KCL, Ohm's law, power balance, and topology checks gate the analyzed-view animation. Wire animation uses a deterministic KCL-consistent routing through traced wires; current inside ideal junctions has no unique physical distribution.
- Editing a source voltage or resistor/bulb resistance triggers a local solve. The overlay updates branch current visuals and component readings; bulb glow responds qualitatively to solved electrical power.
- The workspace keeps the source page visible and supports an overlay view plus a generated circuit-model view. The generated view is disabled for circuits with multiple sources.

Supported circuit families are connected series, parallel, mixed series-parallel, and bridge networks with one or more ideal batteries/cells and known resistor/bulb resistances. Identical ideal sources directly in parallel use an explicitly stated equal-current-sharing assumption; unequal real source sharing needs internal resistance and is not modeled. Bulbs remain distinct components but are solved as fixed resistances; filament heating, rated brightness, and transient behavior are not modeled. Glow is a qualitative visualization because lamp ratings are unknown. Dash pace and thickness are visual mappings of solved current, not literal electron drift speeds. Gemini's image reading is a candidate, not proof of correct topology; inspect connections, especially at crossings and junctions. Unknown resistor/bulb values and non-circuit engineering diagrams are unsupported. Image analysis requires a Gemini API key; circuit solving and value edits are local and do not use Gemini calls.

## Circuit extraction benchmark

Generate the small gold image set with `py backend/tools/circuit_benchmark.py generate backend/tools/benchmark_data`. To score model output, save one JSON object per line in a JSONL file with an `id` from the gold set and a `vision` object, then run `py backend/tools/circuit_benchmark.py score backend/tools/benchmark_data predictions.jsonl`. The report separates component ID/type F1, numeric component-value accuracy (within 1%), and terminal-pair connectivity F1; none of these metrics measures solver accuracy or visual localization.

Run `cd backend; py tools/physics_benchmark.py` to check the deterministic solver against known series, parallel, mixed, and balanced-bridge circuits. This benchmark is separate from image extraction accuracy: passing it shows that the supplied graph is solved correctly, not that an image was read correctly. For extraction comparisons, add manually verified textbook and worksheet examples to the image benchmark and report component/value recognition separately from connection accuracy. These are manual benchmark scripts; the repository does not yet have a maintained automated test suite.

## Run locally (Windows PowerShell)

### Backend

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `backend/.env`, then start the API. `GEMINI_MODEL` defaults to `gemini-3.8-flash`; deployments can override it with a model enabled for their key. PECTEN tries current Gemini model fallbacks if a model is unavailable or overloaded:

```powershell
py -m uvicorn app.main:app --reload
```

The API is at `http://127.0.0.1:8000`; interactive endpoint docs are at `/docs`.

### Frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Vite serves the app at `http://localhost:5173`. The API URL defaults to `http://127.0.0.1:8000`; set `VITE_API_URL` in `frontend/.env.local` to use a different backend.

## API overview

- `GET /health` — backend health check.
- `POST /analyze-circuit` — multipart raster-image upload (12 MB maximum), optional `question`, and optional `X-API-Key`. Returns extracted data and an initial solution; if extraction succeeds but the graph needs repair, it returns the candidate plus `simulation_error`.
- `POST /simulate-circuit` — JSON body `{ "circuit": <vision-shaped data> }`; recalculates edited values and returns component/source results plus physics checks.

Invalid or unsupported circuit data returns a useful 4xx response. Supported circuit JSON is described in [docs/circuit-schema.md](docs/circuit-schema.md).

## Gemini key settings

Users can open **Settings** in the frontend and enter their own Gemini API key. PECTEN keeps it in tab-scoped `sessionStorage` and sends it in the `X-API-Key` header for image analysis. The backend does not persist this user key. Without a user key, the backend uses `GEMINI_API_KEY` from its environment. Image-analysis quota and availability depend on the selected key and Gemini account.

## Project map

- `frontend/src` — React interface, SVG overlays, and API client.
- `backend/app/ai` — Gemini vision prompt and image interpretation.
- `backend/app/api` — FastAPI endpoints.
- `backend/app/physics` — circuit graph, series/parallel reducer, solver, and component result tracing.
- `backend/app/services/analyzer.py` — shared validation and analysis/solve pipeline.
- `docs` — architecture, development, and circuit data contract.

See [docs/architecture.md](docs/architecture.md) for the request flow and known boundaries, and [docs/development.md](docs/development.md) for maintenance notes.
