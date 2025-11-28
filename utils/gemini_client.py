"""Google Gemini API client for Email Productivity Agent."""

import os
import time
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_RETRIES, REQUEST_TIMEOUT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to config)
            model_name: Model name (defaults to config)
        """
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name or GEMINI_MODEL
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure API
        genai.configure(api_key=self.api_key)
        
        # Generation configuration
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        # Safety settings (permissive for business emails)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Initialize model as None - will be created on first use with fallback
        self.model = None
        self.model_name = model_name or GEMINI_MODEL or "models/gemini-flash-latest"
    
    def _discover_available_models(self):
        """Discover available models from the API.
        
        Returns:
            List of available model names
        """
        try:
            all_models = list(genai.list_models())
            available = []
            for model in all_models:
                methods = str(model.supported_generation_methods)
                if 'generateContent' in methods:
                    # Return both formats
                    clean_name = model.name.replace('models/', '')
                    available.append((clean_name, model.name))
            return available
        except Exception as e:
            logger.warning(f"Could not list models: {e}")
            return []
    
    def _get_or_create_model(self, generation_config: Optional[Dict] = None):
        """Get or create model instance, with fallback support.
        
        Args:
            generation_config: Optional generation config override
            
        Returns:
            Model instance
        """
        config = generation_config or self.generation_config
        
        # First, try to discover available models
        available_models = self._discover_available_models()
        
        # Simplified: Use correct model names that actually work
        model_candidates = []
        
        # Try configured model first
        if self.model_name:
            model_candidates.append(self.model_name)
            # Also try without models/ prefix if needed
            if self.model_name.startswith('models/'):
                model_candidates.append(self.model_name.replace('models/', ''))
        
        # Add correct fallbacks (models that actually exist - free tier friendly)
        fallbacks = [
            "models/gemini-flash-latest",  # Free tier - use this first
            "models/gemini-2.0-flash",     # Alternative
            "models/gemini-flash-lite-latest",  # Lightweight
            "models/gemini-pro-latest",    # Pro version
        ]
        
        for model_name in fallbacks:
            if model_name not in model_candidates:
                model_candidates.append(model_name)
        
        # Try each model (no test call - just create instance)
        last_error = None
        
        for model_name in model_candidates:
            try:
                # Create model instance directly
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=config,
                    safety_settings=self.safety_settings,
                    system_instruction="You are an intelligent email processing assistant."
                )
                
                # If we get here, model instance was created
                if model_name != self.model_name:
                    logger.info(f"Using model: {model_name}")
                self.model_name = model_name
                return model
                
            except Exception as e:
                last_error = e
                continue
        
        # If all fail, use first candidate anyway (might work on actual call)
        if model_candidates:
            logger.warning(f"Model initialization had issues, trying {model_candidates[0]} anyway")
            return genai.GenerativeModel(
                model_name=model_candidates[0],
                generation_config=config,
                safety_settings=self.safety_settings,
                system_instruction="You are an intelligent email processing assistant."
            )
        
        raise ValueError(f"Could not create model. Last error: {last_error}")
    
    def generate_completion(self, prompt: str, 
                           system_instruction: Optional[str] = None,
                           temperature: Optional[float] = None,
                           max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate completion from Gemini API.
        
        Args:
            prompt: User prompt
            system_instruction: Optional system instruction override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            Dictionary with 'success', 'response', and 'error' keys
        """
        # Use fewer retries for categorization (faster)
        max_retries = 1 if max_tokens and max_tokens <= 50 else MAX_RETRIES
        retries = 0
        backoff_delay = 0.5  # Reduced backoff
        
        while retries < max_retries:
            try:
                # Override config if provided
                config = self.generation_config.copy()
                if temperature is not None:
                    config["temperature"] = temperature
                if max_tokens is not None:
                    config["max_output_tokens"] = max_tokens
                
                # Get or create model instance (with fallback support)
                # Always use _get_or_create_model to ensure we have a working model
                if self.model is None or temperature is not None or max_tokens is not None:
                    model = self._get_or_create_model(config if (temperature is not None or max_tokens is not None) else None)
                    # Cache the model if using default config
                    if temperature is None and max_tokens is None:
                        self.model = model
                else:
                    model = self.model
                    # If cached model fails, get a new one
                    if model is None:
                        model = self._get_or_create_model()
                        self.model = model
                
                # Generate response - use shorter timeout for faster processing
                timeout = 10 if max_tokens and max_tokens <= 50 else REQUEST_TIMEOUT  # Very short for categorization
                try:
                    response = model.generate_content(
                        prompt,
                        request_options={"timeout": timeout}
                    )
                except Exception as model_error:
                    # If error is about model not found, try getting a new model
                    if "404" in str(model_error) or "not found" in str(model_error).lower():
                        logger.warning(f"Model failed, trying fallback: {model_error}")
                        # Reset cached model and try again with fallback
                        self.model = None
                        model = self._get_or_create_model(config if (temperature is not None or max_tokens is not None) else None)
                        if temperature is None and max_tokens is None:
                            self.model = model
                        timeout = 10 if max_tokens and max_tokens <= 50 else REQUEST_TIMEOUT
                        response = model.generate_content(
                            prompt,
                            request_options={"timeout": timeout}
                        )
                    else:
                        # Re-raise if it's not a model error
                        raise
                
                # Extract text from response
                if response.text:
                    return {
                        'success': True,
                        'response': response.text.strip(),
                        'error': None
                    }
                else:
                    # Handle blocked or empty response
                    if response.candidates and response.candidates[0].finish_reason:
                        finish_reason = response.candidates[0].finish_reason
                        if finish_reason == "SAFETY":
                            return {
                                'success': False,
                                'response': None,
                                'error': 'Response blocked by safety filters'
                            }
                        else:
                            return {
                                'success': False,
                                'response': None,
                                'error': f'Response finished with reason: {finish_reason}'
                            }
                    return {
                        'success': False,
                        'response': None,
                        'error': 'Empty response from API'
                    }
            
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Gemini API call failed (attempt {retries + 1}/{MAX_RETRIES}): {error_msg}")
                
                # Check if it's a rate limit/quota error
                if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    # Extract retry delay from error if available
                    wait_time = 10  # Default wait time
                    if "retry_delay" in error_msg.lower():
                        # Try to extract seconds from error
                        import re
                        delay_match = re.search(r'seconds[:=]\s*(\d+)', error_msg)
                        if delay_match:
                            wait_time = int(delay_match.group(1)) + 2  # Add buffer
                    
                    if retries < MAX_RETRIES - 1:
                        logger.warning(f"⚠️ Rate limit/quota exceeded. Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        # Return early on quota errors instead of retrying
                        return {
                            'success': False,
                            'response': None,
                            'error': f'Quota exceeded. Please wait a few minutes and try again. Error: {error_msg[:100]}'
                        }
                
                retries += 1
                
                if retries >= MAX_RETRIES:
                    return {
                        'success': False,
                        'response': None,
                        'error': f'Failed after {MAX_RETRIES} attempts: {error_msg}'
                    }
                
                # Exponential backoff
                time.sleep(backoff_delay)
                backoff_delay *= 2
        
        return {
            'success': False,
            'response': None,
            'error': 'Max retries exceeded'
        }
    
    def parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response, handling markdown formatting.
        
        Args:
            response_text: Raw response text from Gemini
            
        Returns:
            Parsed JSON dictionary or empty dict if parsing fails
        """
        import json
        import re
        
        try:
            # Strip markdown code blocks
            text = response_text.strip()
            
            # Remove ```json and ``` markers
            text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
            text = text.strip()
            
            # Try to find JSON object in the text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
            
            # Parse JSON
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:200]}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            return {}


