import config
from google import genai

client = genai.Client(api_key=config.GOOGLE_API_KEY)

try:
    models = client.models.list()
    print("Available models:")
    for model in models:
        print(f"  - {model.name}")
except Exception as e:
    print(f"Error listing models: {e}")
