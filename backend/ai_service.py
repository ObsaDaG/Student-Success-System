import os
import time
from collections import deque

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
MAX_PER_MINUTE = int(os.getenv("AI_MAX_PER_MINUTE", "8"))
MAX_PER_DAY = int(os.getenv("AI_MAX_PER_DAY", "150"))

_recent_calls = deque()
_day_start = time.time()
_day_count = 0


def _check_limits():
    global _day_start, _day_count
    now = time.time()

    if now - _day_start > 86400:
        _day_start = now
        _day_count = 0

    while _recent_calls and now - _recent_calls[0] > 60:
        _recent_calls.popleft()

    if len(_recent_calls) >= MAX_PER_MINUTE or _day_count >= MAX_PER_DAY:
        raise RuntimeError("AI call limit reached")

    _recent_calls.append(now)
    _day_count += 1


def generate_text(prompt):
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")

    _check_limits()

    client = genai.Client(api_key=API_KEY)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text


if __name__ == "__main__":
    print(generate_text("Say hello to a university student in one short sentence."))