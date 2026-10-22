import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError
from PIL import Image

load_dotenv()


class GeminiQuotaExceeded(RuntimeError):
    """Raised when Gemini rejects analysis because the API quota is exhausted."""

def get_genai_client(api_key: str = None):
    """Returns a Gemini client using the provided key or the default env key."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("No API key provided and GEMINI_API_KEY not found in .env")
    return genai.Client(api_key=key)

# Keep a default client for internal tests or if no key is provided
try:
    client = get_genai_client()
except ValueError:
    client = None

def get_model_candidates():
    """Return the configured model followed by current stable fallbacks."""
    configured = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    candidates = [configured, "gemini-3.6-flash", "gemini-3.5-flash"]
    return list(dict.fromkeys(model for model in candidates if model))


def generate_with_model_fallback(current_client, contents, config):
    """Retry only for unavailable models, overload, or model-scoped quota errors."""
    failures = []
    for model_name in get_model_candidates():
        try:
            return current_client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        except (ServerError, ClientError) as error:
            if getattr(error, "code", None) not in (404, 429, 503):
                raise
            failures.append(f"{model_name}: {error}")

    raise RuntimeError(
        "No configured Gemini model is currently available. Set GEMINI_MODEL "
        "to a model enabled for this API key. Tried: " + " | ".join(failures)
    )

def test_gemini():
    if not client:
        return "Test failed: no GEMINI_API_KEY is configured."
    try:
        response = generate_with_model_fallback(
            client,
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


def analyze_circuit(image_path: str, api_key: str = None, student_question: str = ""):

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

STUDENT'S QUESTION (if provided):
{student_question or "No question was pasted; read the question visible on the page if possible."}
- Use this question to identify the relevant circuit and requested quantity.
- Keep the supplied wording in problem.text when it is non-empty.
- If the page contains multiple diagrams, focus on the one needed for this question.

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
        "type": "battery | cell | resistor | bulb | switch | ammeter | voltmeter | wire | rheostat | potentiometer | other",
        "value": null,
        "unit": null,

        "terminals": ["1", "2"],

        "polarity": {{
          "terminal_1": null,
          "terminal_2": null
        }},

        "visual": {{
          "bbox": [x1, y1, x2, y2],
          "center": [x, y],
          "terminal_points": {{
            "1": [x1, y1],
            "2": [x2, y2]
          }}
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
    ],

    "nodes": [
      {{
        "id": "N1",
        "terminals": [
          {{"component": "B1", "terminal": "1"}},
          {{"component": "R1", "terminal": "1"}}
        ]
      }}
    ]
  }},

  "visual": {{
    "image_width": {image_width},
    "image_height": {image_height},

    "wire_paths": [
      {{
        "from_component": "B1",
        "from_terminal": "1",
        "to_component": "R1",
        "to_terminal": "1",
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
  ],

  "review_items": [
    {{
      "id": "review-connection-1",
      "kind": "connection",
      "endpoints": [
        {{"component": "R1", "terminal": "1"}},
        {{"component": "R2", "terminal": "2"}}
      ],
      "confidence": "low",
      "reason": "The wire crossing is unclear"
    }},
    {{
      "id": "review-component-1",
      "kind": "component",
      "component": "R1",
      "suggested_type": "resistor",
      "confidence": "medium",
      "reason": "Brief visual ambiguity that needs human confirmation"
    }}
  ]
}}

TERMINAL RULES:
- Every two-terminal component must have terminals "1" and "2".
- Battery polarity must identify which terminal is positive and negative
  when visible.
- Connections must reference component IDs and terminal numbers.
- Also group every component terminal into exactly one electrical node in
  circuit.nodes. Terminals in the same node are electrically connected.
- A wire crossing without a junction dot is NOT a shared node. A visible
  junction dot or continuous joined wire is one shared node.
- circuit.nodes is the authoritative topology. Include isolated terminals as
  single-terminal nodes. Keep connections as pairwise links within each node.
- Do not describe connections using natural-language sentences.
- Return review_items for uncertain component detections or electrical
  connections only. For a component item, include its component ID and
  suggested_type. For a connection item, include exactly two endpoints. Each
  item must use confidence "low" or "medium" and state the visible ambiguity
  briefly.
  Flag crossings without a clear junction dot, obscured wire endpoints, and
  terminals whose connection cannot be distinguished. Do not invent a concern
  when the image is clear. An empty list means no specific visual ambiguity was
  detected; it does not certify that the extracted topology is correct.

VISUAL COMPONENT RULES:
- bbox means [left, top, right, bottom].
- center means the approximate center of the component.
- Coordinates must refer to the ORIGINAL uploaded image.
- Estimate coordinates from the visible diagram.
- Do not use coordinates outside the image.
- Include visual data for every visible circuit component.
- The bounding box should tightly surround the actual component symbol,
  not its text label.
- Estimate the image coordinate of each terminal as terminal_points["1"] and
  terminal_points["2"]. These points must sit at the electrical connection
  ends of the symbol, not at its center.

WIRE PATH RULES:
- Trace visible circuit wires.
- For each wire path, identify the component terminal at both endpoints using
  the component terminal labels. Include from_terminal and to_terminal.
- Keep each path between two terminals; stop at junctions and represent each
  wire segment separately. Do not route through a junction to a different
  component terminal.
- Represent each wire as an ordered list of [x,y] points.
- Use enough points to represent corners and direction changes.
- Points must follow the actual visible wire.
- Do NOT create a theoretical circuit layout.
- Do NOT invent wires that are not visible.
- If the wire geometry cannot be reliably determined, return an empty
  wire_paths array rather than guessing.

VALUE RULES:
- Store only numerical values explicitly visible/stated.
- Classify a visible lamp symbol as "bulb", not "resistor". Bulbs remain a
  distinct component in the extracted model and overlay. For the current DC
  solver, an explicitly stated resistance may be stored as value/unit ohm;
  do not invent a resistance from the symbol or from the requested quantity.
- Examples:
  12 V -> value: 12, unit: "V"
  4 ohm -> value: 4, unit: "ohm"
  2 A -> value: 2, unit: "A"

QUESTION RULES:
- Extract what the problem asks.
- Set problem.asked_quantity to a short canonical quantity such as "current",
  "voltage", "resistance", "power", or "brightness" when the wording makes
  it clear; otherwise use null. Keep component labels or "total" wording in
  problem.text so the solver interface can identify the requested target.
- Examples:
  "find current" -> "current"
  "find voltage across R1" -> "voltage"
  "find power dissipated" -> "power"

Remember:
You are ONLY creating the representation.
The PECTEN physics engine will perform the calculations.
"""

    last_exception = None

    # Use provided API key or fallback to default client
    current_client = get_genai_client(api_key) if api_key else client

    if not current_client:
        raise ValueError("No valid API key available.")

    # Fallback Loop: Try models one by one if we hit a 503 (High Demand)
    for model_name in get_model_candidates():
        try:
            response = current_client.models.generate_content(
                model=model_name,
                contents=[image, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    )
                )
            )
            result = json.loads(response.text)
            if not isinstance(result, dict):
                raise ValueError("Vision extraction must return a JSON object.")
            if not isinstance(result.get("review_items"), list):
                result["review_items"] = []
            return result

        except ServerError as e:
            status_code = getattr(e, "code", None) or getattr(e, "status_code", None)
            if status_code == 429 or "429" in str(e):
                raise GeminiQuotaExceeded(
                    "Gemini API quota or rate limit reached. Add a key with available quota in Settings, "
                    "or wait for the limit to reset."
                ) from e
            # 503 is the "High Demand" error. If we see this, try the next model.
            if "503" in str(e) or status_code == 503:
                last_exception = e
                continue
            # For other server errors, fail immediately
            raise e
        except ClientError as e:
            status_code = getattr(e, "code", None) or getattr(e, "status_code", None)
            if status_code == 429 or "429" in str(e):
                raise GeminiQuotaExceeded(
                    "Gemini API quota or rate limit reached. Add a key with available quota in Settings, "
                    "or wait for the limit to reset."
                ) from e
            if status_code == 404:
                last_exception = e
                continue
            # Invalid keys, permissions, and malformed requests should fail immediately.
            raise e
        except Exception as e:
            raise e

    # If we tried all models and all returned 503
    raise RuntimeError(
        f"No configured Gemini model is currently available. Set GEMINI_MODEL to a model enabled for this API key. "
        f"Last error: {str(last_exception)}"
    )
