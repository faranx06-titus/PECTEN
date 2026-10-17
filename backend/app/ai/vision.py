import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError
from PIL import Image

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

# List of models to try in order of preference
# We start with the latest, then fallback to stable versions
FALLBACK_MODELS = [
    "gemini-3.8-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

def test_gemini():
    # Use the first available model for a simple test
    try:
        response = client.models.generate_content(
            model=FALLBACK_MODELS[0],
            contents="Say hello to PECTEN in one short sentence.",
            config=types.GenerateContentConfig(
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            )
        )
        return response.text
    except Exception as e:
        return f"Test failed: {str(e)}"


def analyze_circuit(image_path: str):

    image = Image.open(image_path)

    # Get the actual image dimensions so Gemini knows the coordinate system.
    image_width, image_height = image.size

    prompt = f"""
You are PECTEN's circuit-vision system.

Your job is to convert a Class 12 Current Electricity problem
containing TEXT and/or a CIRCUIT DIAGRAM into a standardized
machine-readable representation.

IMPORTANT:
- Do NOT solve the physics problem.
- Do NOT calculate current, voltage, power, resistance, etc.
- Only extract information that is explicitly visible or stated.
- If a value is not given, use null.
- Do not invent components or values.
- Return ONLY valid JSON.

IMAGE COORDINATE SYSTEM:
- Image width: {image_width} pixels
- Image height: {image_height} pixels
- Origin (0,0) is the TOP-LEFT corner.
- x increases from LEFT to RIGHT.
- y increases from TOP to BOTTOM.
- All visual coordinates MUST be in the original image's pixel coordinate system.
- Do NOT use normalized coordinates.
- Do NOT use percentages.

Return exactly this structure:

{{
  "problem": {{
    "text": "",
    "asked_quantity": null
  }},

  "circuit": {{
    "type": "series | parallel | mixed | single_loop | unknown",

    "components": [
      {{
        "id": "B1",
        "type": "battery | resistor | switch | ammeter | voltmeter | wire | cell | rheostat | potentiometer | other",
        "value": null,
        "unit": null,

        "terminals": ["1", "2"],

        "polarity": {{
          "terminal_1": null,
          "terminal_2": null
        }},

        "visual": {{
          "bbox": [x1, y1, x2, y2],
          "center": [x, y]
        }}
      }}
    ],

    "connections": [
      {{
        "from": {{
          "component": "B1",
          "terminal": "1"
        }},
        "to": {{
          "component": "R1",
          "terminal": "1"
        }}
      }}
    ]
  }},

  "visual": {{
    "image_width": {image_width},
    "image_height": {image_height},

    "wire_paths": [
      {{
        "from_component": "B1",
        "to_component": "R1",
        "points": [
          [x1, y1],
          [x2, y2],
          [x3, y3]
        ]
      }}
    ]
  }},

  "given_values": [
    {{
      "quantity": "",
      "value": null,
      "unit": ""
    }}
  ],

  "unknowns": [
    {{
      "quantity": ""
    }}
  ]
}}

TERMINAL RULES:
- Every two-terminal component must have terminals "1" and "2".
- Battery polarity must identify which terminal is positive and negative
  when visible.
- Connections must reference component IDs and terminal numbers.
- Do not describe connections using natural-language sentences.

VISUAL COMPONENT RULES:
- bbox means [left, top, right, bottom].
- center means the approximate center of the component.
- Coordinates must refer to the ORIGINAL uploaded image.
- Estimate coordinates from the visible diagram.
- Do not use coordinates outside the image.
- Include visual data for every visible circuit component.
- The bounding box should tightly surround the actual component symbol,
  not its text label.

WIRE PATH RULES:
- Trace visible circuit wires.
- Represent each wire as an ordered list of [x,y] points.
- Use enough points to represent corners and direction changes.
- Points must follow the actual visible wire.
- Do NOT create a theoretical circuit layout.
- Do NOT invent wires that are not visible.
- If the wire geometry cannot be reliably determined, return an empty
  wire_paths array rather than guessing.

VALUE RULES:
- Store only numerical values explicitly visible/stated.
- Examples:
  12 V -> value: 12, unit: "V"
  4 ohm -> value: 4, unit: "ohm"
  2 A -> value: 2, unit: "A"

QUESTION RULES:
- Extract what the problem asks.
- Examples:
  "find current" -> "current"
  "find voltage across R1" -> "voltage"
  "find power dissipated" -> "power"

Remember:
You are ONLY creating the representation.
The PECTEN physics engine will perform the calculations.
"""

    last_exception = None

    # Fallback Loop: Try models one by one if we hit a 503 (High Demand)
    for model_name in FALLBACK_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[image, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    )
                )
            )
            return json.loads(response.text)

        except ServerError as e:
            # 503 is the "High Demand" error. If we see this, try the next model.
            if e.status_code == 503:
                last_exception = e
                continue
            # For other server errors, fail immediately
            raise e
        except ClientError as e:
            # 403 Permission Denied or 400 Bad Request should fail immediately
            raise e
        except Exception as e:
            raise e

    # If we tried all models and all returned 503
    raise RuntimeError(
        f"All Gemini models are currently experiencing high demand. "
        f"Last error: {str(last_exception)}"
    )


 