from fastapi import APIRouter
from app.api.circuit import router as circuit_router

router = APIRouter()

router.include_router(circuit_router)