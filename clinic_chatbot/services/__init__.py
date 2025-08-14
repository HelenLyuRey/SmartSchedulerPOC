"""
Services Package - Responsibilities:
- Provide all business logic services for the chatbot
- Handle external API integrations (LLM, Calendar)
- Process and validate business entities
- Maintain separation between data models and business logic
"""

from .llm_service import LLMService, GeminiService, PromptTemplates

__all__ = ['LLMService', 'GeminiService', 'PromptTemplates']