from fastapi import APIRouter

router = APIRouter()

@router.get("/demo-circuit")
def demo_circuit():

    return {
        "battery": {
            "voltage": 12
        },
        "components": [
            {
                "id": "R1",
                "type": "resistor",
                "current": 3,
                "voltage": 6,
                "power": 18
            },
            {
                "id": "R2",
                "type": "bulb",
                "current": 1,
                "voltage": 6,
                "power": 6
            }
        ]
    }