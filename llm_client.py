import os
from typing import Optional


class MockClient:
    """
    Offline stand-in for an LLM client.
    This lets the app run without an API key.
    """

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        # Very small, predictable behavior for demos.
        if "Return ONLY valid JSON" in system_prompt:
            # Purposely not JSON to force fallback unless students change behavior.
            return "I found some issues, but I'm not returning JSON right now."
        return "# MockClient: no rewrite available in offline mode.\n"


class GeminiClient:
    """
    Minimal Gemini API wrapper with added error resilience.

    Requirements:
    - google-genai installed
    - GEMINI_API_KEY set in environment (or loaded via python-dotenv)
    """

    def __init__(self, model_name: str = "gemini-flash-lite-latest", temperature: float = 0.2):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY. Create a .env file and set GEMINI_API_KEY=..."
            )

        # Import here so heuristic mode doesn't require the dependency at import time.
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.temperature = float(temperature)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a single request to Gemini.

        Errors intentionally propagate to BugHoundAgent, which records the
        failure in its trace and selects the deterministic fallback.
        """
        merged_prompt = f"{system_prompt}\n\n{user_prompt}".strip()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=merged_prompt,
        )

        # Defensive: response.text can be None if the result is blocked.
        return response.text or ""
