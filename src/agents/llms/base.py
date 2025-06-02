from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseLLMClient(ABC):
    """Base class for LLM clients."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate a JSON response from the LLM."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name of the model."""
        pass
    
    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Return the maximum number of tokens the model can handle."""
        pass
    
    @property
    @abstractmethod
    def temperature(self) -> float:
        """Return the temperature setting for the model."""
        pass 