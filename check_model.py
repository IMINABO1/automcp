
import config
from google import genai

client = genai.Client(api_key=config.GOOGLE_API_KEY)
try:
    response = client.models.generate_content(
        model='gemini-3-flash',
        contents='Test'
    )
    print("Success: gemini-3-flash exists!")
except Exception as e:
    print(f"Error: {e}")
