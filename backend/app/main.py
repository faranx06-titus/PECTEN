from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.routes import router
from app.ai.vision import test_gemini
from fastapi import HTTPException
from app.services.analyzer import solve_circuit_data
from app.schemas.simulation import CircuitData

class CircuitSimulationRequest(BaseModel):
    circuit: CircuitData

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
    try:
        _, _, solution = solve_circuit_data(request.circuit.model_dump(exclude_none=False))
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return solution
