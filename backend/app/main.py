from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.api.routes import router

from app.ai.vision import test_gemini
from app.physics.graph_builder import build_circuit_graph
from app.physics.circuit_reducer import CircuitReducer
from app.physics.circuit_solver import CircuitSolver
from app.physics.solution_trace import SolutionTracer
class CircuitSimulationRequest(BaseModel):
    r1_resistance: float
app = FastAPI(
    title="PECTEN",
    description="Interactive Physics Learning Engine",
    version="0.1.0"
)

# Allow the React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "https://pecten-theta.vercel.app",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

@app.get("/")
def root():
    return {
        "message": "PECTEN backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/test-gemini")
def test_gemini_endpoint():
    return {
        "response": test_gemini()
    }

@app.get("/demo-circuit")
def demo_circuit():
    return {
        "circuit_type": "mixed",
        "battery": {
            "id": "B1",
            "voltage": 12,
            "unit": "V"
        },
        "components": [
            {
                "id": "R1",
                "type": "resistor",
                "resistance": 2,
                "unit": "ohm",
                "current": 3,
                "voltage": 6,
                "power": 18
            },
            {
                "id": "R2",
                "type": "bulb",
                "resistance": 6,
                "unit": "ohm",
                "current": 1,
                "voltage": 6,
                "power": 6
            },
            {
                "id": "R3",
                "type": "bulb",
                "resistance": 3,
                "unit": "ohm",
                "current": 2,
                "voltage": 6,
                "power": 12
            }
        ]
    }
@app.post("/simulate-circuit")
def simulate_circuit(request: CircuitSimulationRequest):

    circuit_data = {
        "circuit": {
            "components": [
                {
                    "id": "B1",
                    "type": "battery",
                    "value": 12,
                    "terminals": ["1", "2"]
                },
                {
                    "id": "R1",
                    "type": "resistor",
                    "value": request.r1_resistance,
                    "terminals": ["1", "2"]
                },
                {
                    "id": "R2",
                    "type": "resistor",
                    "value": 6,
                    "terminals": ["1", "2"]
                },
                {
                    "id": "R3",
                    "type": "resistor",
                    "value": 3,
                    "terminals": ["1", "2"]
                }
            ],

            "connections": [
                {
                    "from": {
                        "component": "B1",
                        "terminal": "1"
                    },
                    "to": {
                        "component": "R1",
                        "terminal": "1"
                    }
                },
                {
                    "from": {
                        "component": "R1",
                        "terminal": "2"
                    },
                    "to": {
                        "component": "R2",
                        "terminal": "1"
                    }
                },
                {
                    "from": {
                        "component": "R1",
                        "terminal": "2"
                    },
                    "to": {
                        "component": "R3",
                        "terminal": "1"
                    }
                },
                {
                    "from": {
                        "component": "R2",
                        "terminal": "2"
                    },
                    "to": {
                        "component": "B1",
                        "terminal": "2"
                    }
                },
                {
                    "from": {
                        "component": "R3",
                        "terminal": "2"
                    },
                    "to": {
                        "component": "B1",
                        "terminal": "2"
                    }
                }
            ]
        }
    }

    # 1. Build graph
    graph = build_circuit_graph(circuit_data)

    # 2. Reduce circuit
    reducer = CircuitReducer(graph)
    reducer.reduce_all()

    # 3. Solve total circuit
    solver = CircuitSolver(graph)
    solution = solver.solve_total_current()

    # 4. Trace solution back to original components
    tracer = SolutionTracer(
        graph,
        reducer.reduction_history
    )

    component_results = tracer.trace(
        solution["total_current"]
    )

    return {
        "r1_resistance": request.r1_resistance,
        "voltage": solution["voltage"],
        "equivalent_resistance": solution[
            "equivalent_resistance"
        ],
        "total_current": solution[
            "total_current"
        ],
        "components": component_results
    }

    # Build graph
    graph = build_circuit_graph(circuit_data)

    # Reduce series / parallel combinations
    reducer = CircuitReducer(graph)

    parallel_groups = reducer.find_parallel_groups()

    for group in parallel_groups:
        reducer.reduce_parallel_group(group)

    series_groups = reducer.find_series_groups()

    for group in series_groups:
        reducer.reduce_series_group(group)

    # Solve
    solver = CircuitSolver(graph)

    result = solver.solve_total_current()

    return {
        "r1_resistance": request.r1_resistance,
        "equivalent_resistance": result["equivalent_resistance"],
        "total_current": result["total_current"],
        "voltage": result["voltage"]
    }