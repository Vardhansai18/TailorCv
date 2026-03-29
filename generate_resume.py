from google import genai
import os 
os.environ["GEMINI_API_KEY"] = "AIzaSyCmBaFRBIy9J3EFhAVKFBrCQyl7q798DPg"
# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview", contents="Explain how AI works in a few words"
)
print(response.text)