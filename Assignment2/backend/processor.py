import os
import base64
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def get_page_analysis(url: str, text_content: str, base64_image_data: str) -> str:
    """
    Calls Gemini Flash 2.0 to deeply analyze the webpage's screenshot and textual content.
    base64_image_data: should just be the raw base64 string (no data URL prefix).
    """
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = f"""
    You are a multimodal AI analyzing a web page visit on behalf of a user.
    The user visited: {url}
    
    Here is some text extracted from the page:
    {text_content[:3000]}
    
    Analyze the provided screenshot and the text. 
    1. Describe the visual appearance of the page in fine detail (colors, layout, dark/light theme, UI components).
    2. Identify any notable charts, graphs, images, forms, or distinctive structural elements.
    3. Summarize the semantic meaning, topic, and key information from the text.
    
    Your description will be stored in a vector database for semantic search. Provide a rich, comprehensive paragraph that captures everything a user might later try to search for (e.g. "That website with the dark green header..."). Do not include introductory text, just the detailed description.
    """
    
    image_bytes = base64.b64decode(base64_image_data)
    
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content([
        {"mime_type": "image/jpeg", "data": image_bytes},
        prompt
    ])
    
    return response.text
