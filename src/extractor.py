"""
Extractor - Uses Google Gemini API to extract structured event details from markdown content.
Reused from src/extractor.py
"""
import os
import json
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv
from .models import EventDetail

# Load .env from project root or parent
load_dotenv()
# Also try parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
# Also try grandparent directory (party-scraper root)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("[Extractor] WARNING: GEMINI_API_KEY is not set in .env file")

client = None
model_name = "gemini-2.0-flash"


def _get_client():
    global client
    if client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in .env file")
        client = genai.Client(api_key=api_key)
    return client


def extract_event_detail(content: str) -> Optional[EventDetail]:
    """
    Use Gemini to extract structured event details from markdown/text content.
    
    Args:
        content: The markdown or text content of an event page.
        
    Returns:
        EventDetail model or None on failure.
    """
    prompt = f"""
    You are an expert event data extractor.
    Extract the following information from the provided text content of a party event page.
    Return the result as a JSON object matching this schema:

    {{
        "title": "Name of the event",
        "date": "Date of the event in RRRR-MM-DD format. 'sobota 14. února' will be '2026-02-14'",
        "time": "HH:MM",
        "place": "Venue name",
        "price": "Price info (optional)",
        "description": "Short description",
        "image_url": "Main image URL (optional)"
    }}

    CRITICAL: Output date format '2026-02-14' if text is 'sobota 14. února'
    CRITICAL: Use original langugage.

    If any field is missing, try to infer it from context or use null/empty string appropriately for required fields.

    Content:
    {content[:10000]}
    """

    try:
        c = _get_client()
        response = c.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, top_p=0.95, top_k=64,
                max_output_tokens=8192, response_mime_type="application/json",
            )
        )
        if not response.text:
            print("Empty response from Gemini API")
            return None
        result = json.loads(response.text)
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
        if not isinstance(result, dict):
            print(f"Extraction result is not a mapping: {result}")
            return None
        return EventDetail(**result)
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from Gemini response: {response.text if 'response' in locals() else 'No response'}")
        return None
    except Exception as e:
        print(f"Error during extraction or API call: {e}")
        return None
