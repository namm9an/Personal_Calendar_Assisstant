import os
import json
from typing import Any, Dict, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from .base import BaseLLMClient

class LocalLlama2Client(BaseLLMClient):
    """Client for local Llama2 model."""
    
    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.1"):
        """Initialize the local Llama2 client."""
        self._model_name = model_name
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load model and tokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self._device == "cuda" else torch.float32,
            device_map="auto"
        )
        self._temperature = 0.1  # Low temperature for more deterministic responses
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a text response from the local model."""
        try:
            inputs = self._tokenizer(prompt, return_tensors="pt").to(self._device)
            
            # Generate response
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self._temperature,
                    do_sample=True,
                    **kwargs
                )
            
            response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the prompt from the response
            response = response[len(prompt):].strip()
            return response
        except Exception as e:
            raise RuntimeError(f"Local model generation failed: {str(e)}")
    
    async def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate a JSON response from the local model."""
        try:
            response = await self.generate(prompt, **kwargs)
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Local model JSON generation failed: {str(e)}")
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def max_tokens(self) -> int:
        return 2048  # Mistral-7B's context window
    
    @property
    def temperature(self) -> float:
        return self._temperature 