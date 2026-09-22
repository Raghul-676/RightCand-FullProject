import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
key = os.environ.get("GROQ_API_KEY")
print(f"Key loaded: {bool(key)}, length: {len(key) if key else 0}")

client = Groq(api_key=key)
response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": "Say hello in one word."}],
)
print(response.choices[0].message.content)