import os
from dotenv import load_dotenv
load_dotenv()
k = os.getenv("GEMINI_API_KEY", "")
has_key = bool(k and k != "your_gemini_api_key_here")
print(f"Key set: {has_key}")
print(f"Length: {len(k)}")
