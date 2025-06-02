import os
import json
from typing import Any, Dict, Optional
import google.generativeai as genai
from .base import BaseLLMClient

class GeminiProClient(BaseLLMClient):
    """Client for Google's Gemini Pro model."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini Pro client."""
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=self._api_key)
        self._model = genai.GenerativeModel('gemini-pro')
        self._temperature = 0.1  # Low temperature for more deterministic responses
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a text response from Gemini Pro."""
        try:
            response = await self._model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self._temperature,
                    max_output_tokens=self.max_tokens,
                    **kwargs
                )
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini Pro generation failed: {str(e)}")
    
    async def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate a JSON response from Gemini Pro."""
        try:
            response = await self.generate(prompt, **kwargs)
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Gemini Pro JSON generation failed: {str(e)}")
    
    @property
    def model_name(self) -> str:
        return "gemini-pro"
    
    @property
    def max_tokens(self) -> int:
        return 2048  # Gemini Pro's context window
    
    @property
    def temperature(self) -> float:
        return self._temperature 