from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.schemas.simulation import CircuitModel
from app.schemas.question import QuestionParserModel

from app.api.routes import router
from app.ai.vision import test_gemini
from app.physics.graph_builder import build_circuit_graph
from app.physics.circuit_reducer import CircuitReducer
from app.physics.circuit_solver import CircuitSolver
from app.physics.solution_trace import SolutionTracer

class CircuitSimulationRequest(BaseModel):
    circuit: CircuitModel

app = FastAPI(
    title="PECTEN",
    description="Interactive Physics Learning Engine",
    version="0.1.0"
)

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
    return {"message": "PECTEN backend is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/test-gemini")
def test_gemini_endpoint():
    return {"response": test_gemini()}

@app.post("/simulate-circuit")
def simulate_circuit(request: CircuitSimulationRequest):
    # 1. Build graph from the request model
    graph = build_circuit_graph(request.circuit.dict())

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
        "voltage": solution["voltage"],
        "equivalent_resistance": solution["equivalent_resistance"],
        "total_current": solution["total_current"],
        "components": component_results
    }
