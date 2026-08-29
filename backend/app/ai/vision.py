import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)


def test_gemini():
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="Say hello to PECTEN in one short sentence.",
        config=types.GenerateContentConfig(
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            )
        )
    )

    return response.text

def analyze_circuit(image_path: str):
    image = Image.open(image_path)

    prompt = """
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
- No markdown.
- No ```json fences.

Return exactly this structure:

{
  "problem": {
    "text": "",
    "asked_quantity": null
  },

  "circuit": {
    "type": "series | parallel | mixed | single_loop | unknown",

    "components": [
      {
        "id": "B1",
        "type": "battery | resistor | switch | ammeter | voltmeter | wire | cell | rheostat | potentiometer | other",
        "value": null,
        "unit": null,
        "terminals": ["1", "2"],
        "polarity": {
          "terminal_1": null,
          "terminal_2": null
        }
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
      }
    ]
  },

  "given_values": [
    {
      "quantity": "",
      "value": null,
      "unit": ""
    }
  ],

  "unknowns": [
    {
      "quantity": ""
    }
  ]
}

TERMINAL RULES:
- Every two-terminal component must have terminals "1" and "2".
- Battery polarity must identify which terminal is positive and negative
  when visible.
- Connections must reference component IDs and terminal numbers.
- Do not describe connections using natural-language sentences.

VALUE RULES:
- Store only numerical values explicitly visible/stated.
- Examples:
  12 V -> value: 12, unit: "V"
  4 ohm -> value: 4, unit: "ohm"
  2 A -> value: 2, unit: "A"

QUESTION RULES:
- Extract what the problem asks for.
- Examples:
  "find current" -> "current"
  "find voltage across R1" -> "voltage"
  "find power dissipated" -> "power"

Remember:
You are ONLY creating the representation.
The PECTEN physics engine will perform the calculations.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[image, prompt],
        config=types.GenerateContentConfig(
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            )
        )
    )

    return response.text