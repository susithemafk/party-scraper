import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model_name = "gemini-2.5-flash"

print(f"Testing model: {model_name}...", flush=True)

try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hello, can you hear me?")
    print(f"Success! Response: {response.text}", flush=True)
except Exception as e:
    print(f"Error with {model_name}: {e}", flush=True)

print("Test complete.", flush=True)
