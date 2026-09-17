"""
Google Gemini LLM client with rate limiting and structured JSON output.
"""
import json
import time
import logging
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import config

logger = logging.getLogger(__name__)

# Module-level client (initialized lazily)
_client = None
_last_call_time = 0.0
_min_interval = 60.0 / config.GEMINI_RPM  # seconds between calls


def get_client():
    """Get or create the Gemini client."""
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set. Get one free at https://aistudio.google.com/apikey")
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def _rate_limit():
    """Enforce rate limiting between calls."""
    global _last_call_time
    now = time.time()
    elapsed = now - _last_call_time
    if elapsed < _min_interval:
        sleep_time = _min_interval - elapsed
        logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
        time.sleep(sleep_time)
    _last_call_time = time.time()


@retry(
    stop=stop_after_attempt(config.RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=config.RETRY_DELAY, min=2, max=30),
    retry=retry_if_exception_type((Exception,)),
    before_sleep=lambda retry_state: logger.warning(
        f"LLM call failed, retrying (attempt {retry_state.attempt_number})..."
    ),
)
def call_gemini(prompt: str, system_prompt: str = "", json_mode: bool = True) -> str:
    """
    Call Gemini with rate limiting and retries.
    
    Args:
        prompt: The user prompt
        system_prompt: Optional system instruction
        json_mode: If True, request JSON output
    
    Returns:
        The model's response text
    """
    _rate_limit()
    client = get_client()

    generate_config = types.GenerateContentConfig(
        temperature=config.LLM_TEMPERATURE,
        max_output_tokens=config.LLM_MAX_OUTPUT_TOKENS,
    )

    if system_prompt:
        generate_config.system_instruction = system_prompt

    if json_mode:
        generate_config.response_mime_type = "application/json"

    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
        config=generate_config,
    )

    text = response.text
    if not text:
        raise ValueError("Empty response from Gemini")

    return text


def call_gemini_json(prompt: str, system_prompt: str = "") -> dict:
    """
    Call Gemini and parse the response as JSON.
    
    Returns:
        Parsed JSON dictionary
    """
    text = call_gemini(prompt, system_prompt, json_mode=True)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Gemini response: {text[:200]}")
        # Try to extract JSON from the response
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        raise ValueError(f"Could not parse JSON from response: {e}")
