import base64
import json
import re
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

# Read API key from env
api_key = os.getenv("GROQ_API_KEY")


client = Groq(api_key=api_key)

def classify_art(image_path,model_name="llama-3.3-70b-versatile"):
    
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

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

    

    response = client.chat.completions.create(
        model=model_name,  
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n\nHere is the image (base64 encoded): {image_base64[:500]}..."
            }
        ],
    )

    raw_text = response.choices[0].message.content.strip()

    
    cleaned = re.sub(r"^```json|```$", "", raw_text, flags=re.MULTILINE).strip()

    try:
        data = json.loads(cleaned)
        label = data.get("label")
        details = data.get("details")
        return label, details
    except json.JSONDecodeError:
        return None, raw_text


# label,detail=classify_art("C:/Users/PMLS/Desktop/signature_copy.png")
# print(label)
# print(detail)

# llama-3.3-70b-versatile
# openai/gpt-oss-20b

