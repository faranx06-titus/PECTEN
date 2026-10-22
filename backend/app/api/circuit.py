import os
import tempfile

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.ai.vision import GeminiQuotaExceeded, analyze_circuit
from app.services.analyzer import solve_circuit_data

router = APIRouter()
MAX_UPLOAD_BYTES = 12 * 1024 * 1024


@router.post("/analyze-circuit")
async def analyze_circuit_endpoint(
    file: UploadFile = File(...),
    question: str = Form(default=""),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    if not (file.content_type or "").lower().startswith("image/"):
        raise HTTPException(status_code=415, detail="Upload a circuit image or select a PDF page in PECTEN first.")

    temp_path = None
    try:
        contents = await file.read(MAX_UPLOAD_BYTES + 1)
        if not contents:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")
        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="This image is over the 12 MB limit. Select a smaller crop of the question and circuit.")

        suffix = os.path.splitext(file.filename or "upload.png")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name

        try:
            with Image.open(temp_path) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as error:
            raise HTTPException(status_code=400, detail="The uploaded file is not a readable raster image.") from error

        result = analyze_circuit(temp_path, api_key=x_api_key, student_question=question)
        components = (result.get("circuit") or {}).get("components") if isinstance(result, dict) else None
        if not isinstance(components, list) or not components:
            raise HTTPException(
                status_code=422,
                detail=("PECTEN received the image but could not identify a circuit. Try a sharper crop that includes "
                        "the complete circuit and its values, or upload a clearer image."),
            )
        try:
            graph, reducer, solution = solve_circuit_data(result)
        except (ValueError, KeyError, IndexError, TypeError) as error:
            # Let users inspect and repair a visually misread topology instead
            # of discarding the entire image analysis when the candidate graph
            # is open or electrically unsolvable.
            review_items = result.get("review_items")
            if not isinstance(review_items, list):
                review_items = []
            review_items.append({
                "id": "solver-check",
                "endpoints": [],
                "confidence": "low",
                "reason": f"The candidate topology could not be solved: {error}",
            })
            result["review_items"] = review_items
            return {
                "vision": result,
                "graph": None,
                "reduction_history": [],
                "solution": None,
                "simulation_error": str(error),
            }
        return {
            "vision": result,
            "graph": {"nodes": graph.nodes, "components": graph.components},
            "reduction_history": reducer.reduction_history,
            "solution": solution,
        }
    except HTTPException:
        raise
    except GeminiQuotaExceeded as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    except ValueError as error:
        if "API key" in str(error):
            raise HTTPException(status_code=503, detail="Gemini is not configured. Set GEMINI_API_KEY or provide an API key.") from error
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (KeyError, IndexError, TypeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Circuit analysis failed: {error}") from error
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
