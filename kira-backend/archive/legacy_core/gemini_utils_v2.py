"""
Updated Gemini API Integration using new google.genai package
Migrated from deprecated google.generativeai package
"""

import json
import logging
from typing import List, Dict, Optional
import asyncio

# NEW: Import from google.genai package
import google.genai as genai
from google.genai import types

logger = logging.getLogger(__name__)

class GeminiAPIv2:
    """Updated Gemini API integration with new google.genai package"""
    
    def __init__(self, api_key: str):
        """Initialize Gemini API with new SDK format"""
        # NEW: Configure API with new SDK
        self.client = genai.Client(api_key=api_key)
        self.api_key = api_key
        
        # NEW: Updated model names for new SDK
        self.embedding_model = "models/gemini-embedding-001"  # Correct model name
        self.generative_model = "models/gemini-2.5-flash"  # Latest working model
        
        # Debug: Print available models
        self._debug_available_models()
    
    def _debug_available_models(self):
        """Print available models for debugging"""
        try:
            print("Available Gemini Models (New SDK):")
            # NEW: List models using new SDK
            for model in self.client.models.list():
                if 'embed' in model.name.lower():
                    print(f"  EMBEDDING: {model.name}")
                elif 'gemini' in model.name.lower() and 'generate' in str(model.supported_actions):
                    print(f"  GENERATIVE: {model.name}")
        except Exception as e:
            print(f"Failed to list models: {e}")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding with new SDK format"""
        try:
            # NEW: Embedding generation with new SDK
            result = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(task_type="retrieval_document")
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            if embedding:
                embeddings.append(embedding)
            else:
                # Fallback zero embedding
                embeddings.append([0.0] * 768)
        return embeddings
    
    def generate_content(self, prompt: str) -> Optional[str]:
        """Generate content with new SDK format"""
        try:
            # NEW: Content generation with new SDK
            response = self.client.models.generate_content(
                model=self.generative_model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return None
    
    async def generate_content_async(self, prompt: str) -> Optional[str]:
        """Generate content asynchronously"""
        try:
            # NEW: Async content generation
            response = await self.client.aio.models.generate_content(
                model=self.generative_model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Async content generation failed: {e}")
            return None
    
    def generate_structured_response(self, prompt: str) -> Dict:
        """Generate structured JSON response with fallback"""
        try:
            response_text = self.generate_content(prompt)
            if not response_text:
                return self._error_response("Content generation failed")
            
            # Clean response text
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                return self._error_response(f"Invalid JSON response: {str(e)}")
                
        except Exception as e:
            logger.error(f"Structured response generation failed: {e}")
            return self._error_response(f"API error: {str(e)}")
    
    async def generate_structured_response_async(self, prompt: str) -> Dict:
        """Generate structured JSON response asynchronously"""
        try:
            response_text = await self.generate_content_async(prompt)
            if not response_text:
                return self._error_response("Async content generation failed")
            
            # Clean and parse JSON
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                return self._error_response(f"Invalid JSON response: {str(e)}")
                
        except Exception as e:
            logger.error(f"Async structured response generation failed: {e}")
            return self._error_response(f"API error: {str(e)}")
    
    def _error_response(self, error_message: str) -> Dict:
        """Return standardized error response"""
        return {
            "error": True,
            "error_message": error_message,
            "new_regulatory_changes_detected": False,
            "summary_of_new_changes": f"Analysis failed: {error_message}",
            "industry_impact_assessment": "Unable to assess due to error",
            "financial_impact_projection": "Unable to project due to error",
            "operational_process_changes_required": [],
            "compliance_risk_level": "MEDIUM",
            "workforce_skill_requirements": [],
            "strategic_recommendations": ["Resolve analysis error and retry"],
            "confidence_score": "LOW"
        }

# Global instance for new SDK
_gemini_api_v2 = None

def get_gemini_api_v2() -> GeminiAPIv2:
    """Get or create global Gemini API v2 instance"""
    global _gemini_api_v2
    if _gemini_api_v2 is None:
        from .config import config
        _gemini_api_v2 = GeminiAPIv2(config.gemini_api_key)
    return _gemini_api_v2

# Migration helper functions
def migrate_from_v1_to_v2():
    """Helper function to migrate from old SDK to new SDK"""
    print("Migrating from google.generativeai to google.genai...")
    print("Changes made:")
    print("1. Import: import google.genai as genai (was: import google.generativeai as genai)")
    print("2. Model names: text-embedding-004, gemini-2.0-flash-exp")
    print("3. Embedding: result.embeddings[0].values (was: result['embedding'])")
    print("4. Async support: generate_content_async() added")
    print("5. Model listing: genai.list_models() (updated)")
