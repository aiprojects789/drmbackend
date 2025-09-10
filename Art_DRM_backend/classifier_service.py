from gemini import classify_art as gemini_classify
from open_ai import classify_art as openai_classify
from groq_ai import classify_art as grok_classify

async def classify_image(image_path: str, model_choice: str = "auto"):
    if model_choice == "gemini-1.5-flash":
        return {"provider": "gemini-flash", "result": gemini_classify(image_path, "gemini-1.5-flash")}
    if model_choice == "gemini-1.5-pro":
        return {"provider": "gemini-pro", "result": gemini_classify(image_path, "gemini-1.5-pro")}
    if model_choice == "openai-gpt4.1":
        return {"provider": "openai", "result": openai_classify(image_path, "gpt-4.1")}
    if model_choice == "groq-llama-3.3-70b":
        return {"provider": "groq-llama", "result": grok_classify(image_path, "llama-3.3-70b-versatile")}
    if model_choice == "groq-gpt-oss-20b":
        return {"provider": "groq-oss", "result": grok_classify(image_path, "openai/gpt-oss-20b")}

    # auto Fallback
    try:
        return {"provider": "gemini-flash", "result": gemini_classify(image_path, "gemini-1.5-flash")}
    except:
        pass
    try:
        return {"provider": "gemini-pro", "result": gemini_classify(image_path, "gemini-1.5-pro")}
    except:
        pass
    try:
        return {"provider": "openai", "result": openai_classify(image_path, "gpt-4.1")}
    except:
        pass
    try:
        return {"provider": "groq-llama", "result": grok_classify(image_path, "llama-3.3-70b-versatile")}
    except:
        pass
    try:
        return {"provider": "groq-oss", "result": grok_classify(image_path, "openai/gpt-oss-20b")}
    except:
        pass

    return {"provider": None, "result": None}
