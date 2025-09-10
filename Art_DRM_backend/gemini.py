
import google.generativeai as genai
from PIL import Image
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

# Read API key from env
api_key = os.getenv("GEMINI_API_KEY")
print(api_key)



# API key
genai.configure(api_key=api_key)



def classify_art(image_path,model_name="gemini-1.5-flash"):
    model = genai.GenerativeModel(model_name)
    img = Image.open(image_path)

    prompt = """
You are an expert art analyst.
Your task is to classify an image as either AI-generated or Real (human-made).

🔍 Analysis Guide (do this in your mind, do NOT show steps in output):
- AI-generated images often show overly smooth or perfect details, unnatural symmetry, inconsistent brush/pen strokes, or surreal textures.
- Real artworks have natural imperfections, authentic brush or pencil strokes, physical texture (paper/canvas/paint), or natural digital design patterns.

🎯 Rules:
1. Choose exactly one label: "AI" or "Real".
2. Always provide a subtype/description in "details":
   - If "Real", possible subtypes: "Hand-painted artwork", "Hand-drawn artwork", "Digital Graphic" , etc or anything that you can think.
   - If "AI", possible subtypes: "AI digital artwork", "AI photo-realistic render", "AI abstract art", etc or anything that you can think.
3. Do not explain, do not use markdown, do not add extra text.

✅ Output strictly in JSON:
{
  "label": "AI" or "Real",
  "details": "Subtype or description"
}

"""


    response = model.generate_content([prompt, img])

    raw_text = response.text.strip()

    # to clean json block
    cleaned = re.sub(r"^```json|```$", "", raw_text, flags=re.MULTILINE).strip()

    try:
        data = json.loads(cleaned)
        label = data.get("label")
        details = data.get("details")
        return label, details
    except json.JSONDecodeError:
        # fallback: if not parse than return raw data
        return None, raw_text




# gemini-1.5-pro
# gemini-1.5-flash