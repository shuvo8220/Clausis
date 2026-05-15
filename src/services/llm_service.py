"""
LLM Service - Abstraction Layer for Language Models
----------------------------------------------------
Follows SOLID principles:
- Single Responsibility: Handles only LLM interactions
- Open/Closed: Easy to extend with new providers
- Liskov Substitution: All providers implement same interface
- Interface Segregation: Clean, minimal interface
- Dependency Inversion: Depends on abstractions, not concretions
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    GROQ = "groq"


class LLMResponse:
    """Standardized response from any LLM provider"""
    def __init__(self, content: str, model: str, usage: Optional[dict] = None):
        self.content = content
        self.model = model
        self.usage = usage or {}


class BaseLLMService(ABC):
    """Abstract base class for LLM services"""
    
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the current model name"""
        pass


class OpenAILLMService(BaseLLMService):
    """OpenAI GPT implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"Initialized OpenAI service with model: {model}")
    
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            
            return LLMResponse(content=content, model=self.model, usage=usage)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def get_model_name(self) -> str:
        return self.model


class GroqLLMService(BaseLLMService):
    """Groq implementation"""
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model = model
        logger.info(f"Initialized Groq service with model: {model}")
    
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate using Groq API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            
            return LLMResponse(content=content, model=self.model, usage=usage)
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    def get_model_name(self) -> str:
        return self.model


class LLMServiceFactory:
    """Factory for creating LLM services (Factory Pattern)"""
    
    @staticmethod
    def create(
        provider: LLMProvider,
        api_key: str,
        model: Optional[str] = None
    ) -> BaseLLMService:
        """Create an LLM service based on provider"""
        
        if provider == LLMProvider.OPENAI:
            return OpenAILLMService(
                api_key=api_key,
                model=model or "gpt-4o"
            )
        elif provider == LLMProvider.GROQ:
            return GroqLLMService(
                api_key=api_key,
                model=model or "llama-3.3-70b-versatile"
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


# Singleton instance
_llm_service: Optional[BaseLLMService] = None


def get_llm_service() -> BaseLLMService:
    """Get or create the LLM service singleton"""
    global _llm_service
    
    if _llm_service is None:
        from ..config import settings
        
        # Determine provider and credentials
        provider = LLMProvider(settings.llm_provider)
        
        if provider == LLMProvider.OPENAI:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            api_key = settings.openai_api_key
            model = settings.openai_model
        else:  # GROQ
            if not settings.groq_api_key:
                raise ValueError("GROQ_API_KEY not configured")
            api_key = settings.groq_api_key
            model = settings.groq_model
        
        _llm_service = LLMServiceFactory.create(provider, api_key, model)
        logger.info(f"LLM service initialized: {provider.value} - {model}")
    
    return _llm_service


def reset_llm_service():
    """Reset the singleton (useful for testing)"""
    global _llm_service
    _llm_service = None
