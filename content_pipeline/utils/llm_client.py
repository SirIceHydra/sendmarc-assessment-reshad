"""
LLM Client - Wrapper for Google Gemini API
"""
import os
import json
import time
from typing import Optional, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    """Client for interacting with Google Gemini API"""
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        # Using gemini-2.0-flash (non-experimental) for free tier support
        # gemini-2.0-flash-exp has no free tier quota
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
    def call_gemini(
        self, 
        prompt: str, 
        system: Optional[str] = None, 
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> str:
        """
        Call Gemini API with retry logic and rate limiting
        
        Args:
            prompt: User prompt
            system: System instructions
            temperature: Generation temperature (0.0-1.0)
            max_retries: Number of retries on failure
            
        Returns:
            Generated text response
        """
        for attempt in range(max_retries):
            try:
                # Add delay between attempts to respect rate limits
                if attempt > 0:
                    wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60s
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=16000,  # Increased for longer articles (up to ~4000 words)
                )
                
                # Combine system and user prompts
                full_prompt = prompt
                if system:
                    full_prompt = f"{system}\n\n{prompt}"
                
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                
                # Small delay after successful call to respect rate limits
                time.sleep(0.5)
                
                return response.text
                
            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    # Extract retry delay if available
                    import re
                    retry_match = re.search(r'retry.*?(\d+\.?\d*)\s*s', error_str, re.IGNORECASE)
                    if retry_match:
                        wait_time = float(retry_match.group(1)) + 5  # Add buffer
                    else:
                        wait_time = min(60 * (attempt + 1), 120)  # Max 2 minutes
                    
                    print(f"⚠ Rate limit hit. Waiting {wait_time:.1f} seconds...")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"Rate limit exceeded. Please wait a few minutes and try again. Error: {error_str[:200]}")
                
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                    print(f"API call failed (attempt {attempt + 1}/{max_retries}): {error_str[:200]}")
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Gemini API call failed after {max_retries} attempts: {error_str[:200]}")
    
    def call_with_structured_output(
        self, 
        prompt: str, 
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Call Gemini and parse JSON response
        
        Args:
            prompt: User prompt (should request JSON output)
            system: System instructions
            temperature: Generation temperature
            
        Returns:
            Parsed JSON dictionary
        """
        response_text = self.call_gemini(prompt, system, temperature)
        
        # Extract JSON from response (handle markdown code blocks)
        json_text = response_text.strip()
        
        # Remove markdown code block markers if present
        if json_text.startswith('```'):
            lines = json_text.split('\n')
            # Remove first line (```json or ```}
            lines = lines[1:]
            # Remove last line if it's just ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            json_text = '\n'.join(lines)
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            # Try to find JSON object in text
            start_idx = json_text.find('{')
            end_idx = json_text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_text = json_text[start_idx:end_idx + 1]
                return json.loads(json_text)
            else:
                raise ValueError(f"Failed to parse JSON from response: {e}\nResponse: {response_text}")


# Global instance
_client = None

def get_client() -> GeminiClient:
    """Get or create global Gemini client instance"""
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client


def call_gemini(prompt: str, system: Optional[str] = None, temperature: float = 0.7) -> str:
    """Convenience function for calling Gemini"""
    client = get_client()
    return client.call_gemini(prompt, system, temperature)


def call_with_structured_output(
    prompt: str, 
    system: Optional[str] = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """Convenience function for structured output"""
    client = get_client()
    return client.call_with_structured_output(prompt, system, temperature)

