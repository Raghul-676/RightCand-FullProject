# import os
# import time
# from dotenv import load_dotenv
# from groq import Groq, APIError, APIConnectionError, RateLimitError

# # Load .env file from project root (works regardless of where app is launched from)
# load_dotenv()

# MODEL = "llama-3.1-8b-instant"

# def _get_client() -> Groq:
#     """Initialize and return a Groq client. Raises if API key is missing."""
#     api_key = os.environ.get("GROQ_API_KEY")
#     if not api_key:
#         raise EnvironmentError(
#             "GROQ_API_KEY environment variable is not set. "
#             "Please set it before running the application."
#         )
#     return Groq(api_key=api_key)


# def generate_response(prompt: str) -> str:
#     """Send a prompt to the Groq LLM and return the text response with retry logic."""
#     max_retries = 3
#     base_delay = 2.0
#     for attempt in range(max_retries):
#         try:
#             client = _get_client()
#             response = client.chat.completions.create(
#                 model=MODEL,
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.7,
#             )
#             return response.choices[0].message.content.strip()
#         except EnvironmentError:
#             raise
#         except RateLimitError as e:
#             if attempt < max_retries - 1:
#                 time.sleep(base_delay * (2 ** attempt))
#                 continue
#             raise RuntimeError(f"Groq API rate limit exceeded after {max_retries} attempts: {e}")
#         except APIConnectionError as e:
#             if attempt < max_retries - 1:
#                 time.sleep(base_delay * (2 ** attempt))
#                 continue
#             raise RuntimeError("Unable to connect to Groq API. Check your internet connection.")
#         except APIError as e:
#             if attempt < max_retries - 1:
#                 time.sleep(base_delay * (2 ** attempt))
#                 continue
#             raise RuntimeError(f"Groq API error: {e}")
#         except Exception as e:
#             raise RuntimeError(f"Unexpected error calling LLM: {e}")


import os
import time
from dotenv import load_dotenv
from groq import Groq, APIError, APIConnectionError, RateLimitError

# Load .env file from project root (works regardless of where app is launched from)
load_dotenv()

MODEL = "openai/gpt-oss-120b"

def _get_client() -> Groq:
    """Initialize and return a Groq client. Raises if API key is missing."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY environment variable is not set. "
            "Please set it before running the application."
        )
    return Groq(api_key=api_key)


def generate_response(prompt: str) -> str:
    """Send a prompt to the Groq LLM and return the text response with retry logic."""
    max_retries = 3
    base_delay = 2.0
    for attempt in range(max_retries):
        try:
            client = _get_client()
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except EnvironmentError:
            raise
        except RateLimitError as e:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise RuntimeError(f"Groq API rate limit exceeded after {max_retries} attempts: {e}")
        except APIConnectionError as e:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise RuntimeError("Unable to connect to Groq API. Check your internet connection.")
        except APIError as e:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise RuntimeError(f"Groq API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error calling LLM: {e}")


def generate_json_response(prompt: str, model: str = None) -> str:
    """
    Same retry behavior as generate_response, but forces the Groq API to
    constrain output to valid JSON via response_format, and lowers
    temperature for more consistent structure. Use this for any agent whose
    prompt asks for a JSON object back (resume_agent, jd_agent, gap_agent,
    evaluation_agent), instead of generate_response.

    Accepts an optional model override — openai/gpt-oss-120b (the current
    default MODEL) is noticeably less reliable at strict JSON formatting
    than the 120B model, even with response_format set. If failures persist
    after this change, pass model="openai/gpt-oss-120b" for these four
    JSON-dependent agents specifically, since correctness matters more than
    the smaller model's speed advantage for these calls.
    """
    max_retries = 3
    base_delay = 2.0
    use_model = model or MODEL
    for attempt in range(max_retries):
        try:
            client = _get_client()
            response = client.chat.completions.create(
                model=use_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content.strip()
        except EnvironmentError:
            raise
        except RateLimitError as e:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise RuntimeError(f"Groq API rate limit exceeded after {max_retries} attempts: {e}")
        except APIConnectionError as e:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise RuntimeError("Unable to connect to Groq API. Check your internet connection.")
        except APIError as e:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise RuntimeError(f"Groq API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error calling LLM: {e}")