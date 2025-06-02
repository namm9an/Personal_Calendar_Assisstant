import os
import logging
from typing import Optional
from uuid import UUID
from prometheus_client import Counter, Histogram
from .llms.gemini import GeminiProClient
from .llms.llama2 import LocalLlama2Client
from .llms.base import BaseLLMClient

# Set up logging
logger = logging.getLogger(__name__)

# Prometheus metrics
LLM_FALLBACK_COUNTER = Counter(
    'agent_llm_fallback_count',
    'Number of times LLM fallback occurred',
    ['user_id', 'from_model', 'to_model']
)

LLM_CALL_LATENCY = Histogram(
    'agent_llm_call_latency_seconds',
    'Time spent in LLM calls',
    ['model_name']
)

class LLMSelector:
    """Selects and manages LLM clients with fallback logic."""
    
    def __init__(self):
        """Initialize the LLM selector."""
        self._force_local = os.getenv("FORCE_LOCAL_LLM", "").lower() == "true"
        self._gemini_client = None
        self._local_client = None
    
    def _get_gemini_client(self) -> GeminiProClient:
        """Get or create the Gemini Pro client."""
        if self._gemini_client is None:
            self._gemini_client = GeminiProClient()
        return self._gemini_client
    
    def _get_local_client(self) -> LocalLlama2Client:
        """Get or create the local Llama2 client."""
        if self._local_client is None:
            self._local_client = LocalLlama2Client()
        return self._local_client
    
    def _user_quota_remaining(self, user_id: UUID) -> int:
        """Check if user has remaining quota for Gemini Pro.
        
        This is a placeholder implementation. In a real system, you would:
        1. Query a database or cache for the user's quota
        2. Consider factors like subscription tier, usage history, etc.
        3. Implement rate limiting and quota management
        """
        # For now, return a fixed quota of 100 calls per user
        return 100
    
    async def get_llm(self, user_id: UUID) -> BaseLLMClient:
        """Get an LLM client instance with fallback logic."""
        if self._force_local:
            logger.info(f"Using local model for user {user_id} (FORCE_LOCAL_LLM=true)")
            return self._get_local_client()
        
        try:
            if self._user_quota_remaining(user_id) > 0:
                logger.info(f"Using Gemini Pro for user {user_id}")
                return self._get_gemini_client()
        except Exception as e:
            logger.warning(f"Failed to check quota for user {user_id}: {str(e)}")
        
        logger.info(f"Falling back to local model for user {user_id}")
        LLM_FALLBACK_COUNTER.labels(
            user_id=str(user_id),
            from_model="gemini-pro",
            to_model="mistral-7b"
        ).inc()
        return self._get_local_client()
    
    async def generate_with_fallback(
        self,
        user_id: UUID,
        prompt: str,
        is_json: bool = False,
        **kwargs
    ) -> str | dict:
        """Generate a response with automatic fallback if the primary model fails."""
        llm = await self.get_llm(user_id)
        
        try:
            with LLM_CALL_LATENCY.labels(model_name=llm.model_name).time():
                if is_json:
                    return await llm.generate_json(prompt, **kwargs)
                return await llm.generate(prompt, **kwargs)
        except Exception as e:
            if isinstance(llm, GeminiProClient):
                logger.warning(f"Gemini Pro failed for user {user_id}, falling back to local model: {str(e)}")
                LLM_FALLBACK_COUNTER.labels(
                    user_id=str(user_id),
                    from_model="gemini-pro",
                    to_model="mistral-7b"
                ).inc()
                
                # Try with local model
                local_llm = self._get_local_client()
                with LLM_CALL_LATENCY.labels(model_name=local_llm.model_name).time():
                    if is_json:
                        return await local_llm.generate_json(prompt, **kwargs)
                    return await local_llm.generate(prompt, **kwargs)
            else:
                # If local model fails, re-raise the exception
                raise RuntimeError(f"Local model generation failed: {str(e)}") 