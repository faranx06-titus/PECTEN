
from fastapi import APIRouter, UploadFile, File
import tempfile
import os

from app.ai.vision import analyze_circuit
from app.physics.graph_builder import build_circuit_graph
from app.physics.circuit_reducer import CircuitReducer
from app.physics.circuit_solver import CircuitSolver
from app.physics.solution_trace import SolutionTracer

router = APIRouter()


@router.post("/analyze-circuit")
async def analyze_circuit_endpoint(
    file: UploadFile = File(...)
):
    suffix = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp_file:

        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        # Step 1: Gemini Vision
        result = analyze_circuit(temp_path)

        # Step 2: Convert Gemini JSON → CircuitGraph
        graph = build_circuit_graph(result)
        reducer = CircuitReducer(graph)
        reducer.reduce_all()
        solver = CircuitSolver(graph)
        solution = solver.solve_total_current()
        tracer = SolutionTracer(
              graph,
              reducer.reduction_history
        )
        component_results = tracer.trace(
            solution["total_current"]
                            )

        
        return {
            "vision": result,
            "graph": {
                "nodes": graph.nodes,
                "components": graph.components
            },
            "reduction_history": reducer.reduction_history,
            "solution": solution,
            "component_results": component_results

          
            
        }

    finally:
        os.remove(temp_path)
