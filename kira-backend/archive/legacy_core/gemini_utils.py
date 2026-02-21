"""
Gemini API Utilities - Fixed Integration
Properly configured with latest models and error handling
"""

import json
import logging
from typing import List, Dict, Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiAPI:
    """Fixed Gemini API integration with proper model names"""
    
    def __init__(self, api_key: str):
        """Initialize Gemini API with proper configuration"""
        genai.configure(api_key=api_key)
        self.api_key = api_key
        
        # Initialize models
        self.embedding_model = "models/gemini-embedding-001"
        self.generative_model = "models/gemini-flash-latest"
        
        # Debug: Print available models
        self._debug_available_models()
    
    def _debug_available_models(self):
        """Print available models for debugging"""
        try:
            print("Available Gemini Models:")
            for model in genai.list_models():
                print(f"  {model.name} - {model.supported_generation_methods}")
                if 'gemini-1.5-flash' in model.name.lower():
                    print(f"    *** FOUND FLASH MODEL: {model.name}")
                if 'gemini-embedding' in model.name.lower():
                    print(f"    *** FOUND EMBEDDING MODEL: {model.name}")
        except Exception as e:
            print(f"Failed to list models: {e}")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding with proper error handling"""
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return result["embedding"]
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
        """Generate content with proper error handling"""
        try:
            model = genai.GenerativeModel(self.generative_model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
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

# Global instance
_gemini_api = None

def get_gemini_api() -> GeminiAPI:
    """Get or create global Gemini API instance"""
    global _gemini_api
    if _gemini_api is None:
        from .config import config
        _gemini_api = GeminiAPI(config.gemini_api_key)
    return _gemini_api
