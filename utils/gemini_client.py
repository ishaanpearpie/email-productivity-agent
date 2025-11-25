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
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            system_instruction="You are an intelligent email processing assistant."
        )
    
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
        retries = 0
        backoff_delay = 1
        
        while retries < MAX_RETRIES:
            try:
                # Override config if provided
                config = self.generation_config.copy()
                if temperature is not None:
                    config["temperature"] = temperature
                if max_tokens is not None:
                    config["max_output_tokens"] = max_tokens
                
                # Create model with custom config if needed
                if temperature is not None or max_tokens is not None:
                    model = genai.GenerativeModel(
                        model_name=self.model_name,
                        generation_config=config,
                        safety_settings=self.safety_settings,
                        system_instruction=system_instruction or "You are an intelligent email processing assistant."
                    )
                else:
                    model = self.model
                
                # Generate response
                response = model.generate_content(
                    prompt,
                    request_options={"timeout": REQUEST_TIMEOUT}
                )
                
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
                
                # Check if it's a rate limit error
                if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    if retries < MAX_RETRIES - 1:
                        wait_time = backoff_delay * (2 ** retries)
                        logger.info(f"Rate limited. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        backoff_delay *= 2
                
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


