import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


def generate_text(prompt):
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")

    client = genai.Client(api_key=API_KEY)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text


if __name__ == "__main__":
    print(generate_text("Say hello to a university student in one short sentence."))