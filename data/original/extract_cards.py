# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "google-genai",
#     "Pillow",
#     "python-dotenv",
# ]
# ///

import os
import json
import argparse
from io import BytesIO
from dotenv import load_dotenv
from PIL import Image
from google import genai
from google.genai import types

load_dotenv()


def compress_image(image_path, max_size=1600, quality=90):
    """Open, optionally resize, and re-encode the image to reduce token usage."""
    img = Image.open(image_path)
    # Convert palette orRGBA with transparency to RGB for JPEG
    if img.mode in ("P", "RGBA", "LA", "L"):
        img = img.convert("RGB")
    width, height = img.size
    largest = max(width, height)
    if largest > max_size:
        ratio = max_size / largest
        new_size = (int(width * ratio), int(height * ratio))
        # img = img.resize(new_size, Image.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)
    return buffer.read()


# Schema to enforce structured JSON responses from Gemini
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "cards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "position": {
                        "type": "object",
                        "description": "In this object, you must define the position of the card. It starts at {row: 1, col: 1}. Each position must be unique.",
                        "properties": {
                            "row": {"type": "number"},
                            "col": {"type": "number"},
                        },
                        "required": ["row", "col"],
                    },
                    "prompt_top": {
                        "type": "string",
                        "description": "The text of the TOP prompt for that CARD. It MUST contain the <green>...</green> tag and the <red>...</red> tag to reflect the highlighted elements in the card's prompt. Make sure the colors match the tags.",
                        "example": "Te han detenido por cavar un túnel desde tu casa hasta el banco de España. Solo puedes hacer una llamada. ¿A quién llamas? De <green>menos lógico</green> a <red>más lógico</red>.",
                    },
                    "prompt_bottom": {
                        "type": "string",
                        "description": "The text of the BOTTOM prompt for that CARD. It MUST contain the <green>...</green> tag and the <red>...</red> tag to reflect the highlighted elements in the card's prompt. Make sure the colors match the tags.",
                        "example": "Te han detenido por cavar un túnel desde tu casa hasta el banco de España. Solo puedes hacer una llamada. ¿A quién llamas? De <green>menos lógico</green> a <red>más lógico</red>.",
                    },
                },
                "propertyOrdering": ["position", "prompt_top", "prompt_bottom"],
                "required": ["position", "prompt_top", "prompt_bottom"],
            },
        }
    },
    "propertyOrdering": ["cards"],
    "required": ["cards"],
}

SYSTEM_PROMPT = """The following image is a picture taken of a list of cards from a game called TopTen. It is in spanish.
I want you to identify each card separately, and extract their content in a formatted structure.

- You MUST identify the green and red text on each prompt, and translate it into the response using <green> and <red> correspondly. It is extremely important the tag matches the color of the card. BE CAREFUL ABOUT IT.
- When wrapping the text in the green and red tags, it is extremely important that only the text that is actually green and red is wrapped, and not a single word out of it.
- The output contains a position object that matches a matrix/grid, just like the image. Make sure you translate this structure from the image to the JSON.
- The word CAPITEN is correct, it does not have a typo. It is often underlined in the cards, so you can use `<u>CAPITEN</u>`.
- Some cards have the characters `«` and `»`. Feel free to use them.

Return a JSON object with a single key "cards" which is an array of objects. Each object should have:
- position (object with row and col integer properties)
- prompt_top (string)
- prompt_bottom (string)

Important!: prompts (top and bottom) are never empty. You must always detect and extract the content."""

EXAMPLE_OUTPUT = """{
  "cards": [
    {
      "position": {"row": 1, "col": 1},
      "prompt_top": "TE HAN DETENIDO POR CAVAR UN TÚNEL DESDE TU CASA HASTA EL BANCO DE ESPAÑA. SOLO PUEDES HACER UNA LLAMADA. ¿A QUIÉN LLAMAS? DE <green>MENOS LÓGICO</green> A <red>MÁS LÓGICO</red>.",
      "prompt_bottom": "DILE «¡BU!» A QUIÉN TÚ ELIJAS. DE SUSTO <green>SUPERADORABLE</green> A <red>SUPERESCALOFRIANTE</red>."
    },
    {
      "position": {"row": 1, "col": 2},
      "prompt_top": "¿DÓNDE TE ESCONDERÍAS DURANTE UNA INVASIÓN ZOMBI? DE <green>SUPERVIVENCIA ASEGURADA</green> A <red>MUERTE SEGURA</red>.",
      "prompt_bottom": "EL <u>CAPITEN</u> SE HA PERDIDO EN MITAD DE LA JUNGLA, LEJOS DE TODA CIVILIZACIÓN. ESTÁ CLARO QUE VA A TENER QUE VIVIR EL RESTO DE SU VIDA COMO TARZÁN. ¿QUÉ ECHARÁ MÁS DE MENOS? DE <green>UN POCO</green> A <red>MUCHÍSIMO</red>."
    }
  ]
}"""


def parse_response_text(response_text):
    """Strip markdown fences and parse JSON."""
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    return json.loads(response_text.strip())


def extract_cards(image_path):
    token = os.environ.get("GEMINI_TOKEN")
    if not token:
        raise ValueError("GEMINI_TOKEN is not set in the environment or .env file.")

    client = genai.Client(api_key=token)

    compressed_image = compress_image(image_path)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=RESPONSE_SCHEMA,
    )

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="Please output the required JSON structure."),
            ],
        ),
        types.Content(
            role="model",
            parts=[types.Part.from_text(text=EXAMPLE_OUTPUT)],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="Extract the cards from this image."),
                types.Part.from_bytes(data=compressed_image, mime_type="image/jpeg"),
            ],
        ),
    ]

    response_text = ""
    try:
        print("Generating response...")
        for chunk in client.models.generate_content_stream(
            model="gemini-3.1-flash-lite",
            contents=contents,
            config=config,
        ):
            if chunk.text:
                print(chunk.text, end="", flush=True)
                response_text += chunk.text
        print("\n")
    except Exception as e:
        print(f"API Error during streaming: {e}")
        print("Retrying without streaming for better error context...")
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=contents,
                config=config,
            )
            response_text = response.text
            print(response_text)
        except Exception as e2:
            print(f"Fallback request also failed: {e2}")
            return None

    try:
        data = parse_response_text(response_text)
        return data
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response was:\n{response_text}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Extract game cards from an image.")
    parser.add_argument("--input", required=True, help="Input image path (e.g., game_cards/1_A.jpeg)")
    parser.add_argument("--output", required=True, help="Output directory path (e.g., output/)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        return

    os.makedirs(args.output, exist_ok=True)

    print(f"Processing '{args.input}'...")
    data = extract_cards(args.input)

    if data:
        filename = os.path.basename(args.input)
        name, _ = os.path.splitext(filename)
        output_file = os.path.join(args.output, f"{name}.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Successfully saved to '{output_file}'")
    else:
        print("Failed to extract cards.")


if __name__ == "__main__":
    main()
