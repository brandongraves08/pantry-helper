import base64
import json
import logging
import os
from typing import Optional
from app.models.schemas import VisionOutput
from app.exceptions import VisionAnalysisError

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """
    Multi-provider vision API handler for pantry image analysis.
    Supports OpenAI GPT-4 Vision and Google Gemini.
    """

    def __init__(self, api_key: str = None, provider: str = None):
        """
        Initialize vision analyzer with specified provider.
        
        Args:
            api_key: API key for the vision provider
            provider: 'openai' or 'gemini' (auto-detected from env if not specified)
        """
        self.provider = provider or os.getenv("VISION_PROVIDER", "openai").lower()
        self.api_key = api_key or self._get_api_key()
        self.max_retries = 3
        
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "gemini":
            self._init_gemini()
        else:
            raise ValueError(f"Unsupported vision provider: {self.provider}")
    
    def _get_api_key(self) -> str:
        """Get API key from environment based on provider"""
        if self.provider == "openai":
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            return key
        elif self.provider == "gemini":
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("GEMINI_API_KEY is required for Gemini provider")
            return key
        return ""
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-4-vision-preview")
            logger.info(f"Initialized OpenAI vision with model: {self.model}")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def _init_gemini(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            self.client = genai.GenerativeModel(self.model)
            logger.info(f"Initialized Gemini vision with model: {self.model}")
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")

    def analyze_image(self, image_path: str) -> VisionOutput:
        """
        Analyze a pantry image and extract inventory items.
        
        Args:
            image_path: Path to the JPEG image file
            
        Returns:
            VisionOutput with parsed items and confidence scores
            
        Raises:
            VisionAnalysisError: If analysis fails
        """
        logger.info(f"Analyzing image with {self.provider}: {image_path}")
        
        try:
            if self.provider == "openai":
                return self._analyze_openai(image_path)
            elif self.provider == "gemini":
                return self._analyze_gemini(image_path)
        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            raise VisionAnalysisError(f"Image file not found: {image_path}")
        except Exception as e:
            logger.exception(f"Unexpected error during image analysis: {str(e)}")
            raise VisionAnalysisError(f"Unexpected error: {str(e)}")
    
    def _analyze_openai(self, image_path: str) -> VisionOutput:
        """Analyze image using OpenAI GPT-4 Vision"""
        from openai import APIError, APIConnectionError, RateLimitError
        
        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}",
                                    "detail": "high",
                                },
                            },
                            {
                                "type": "text",
                                "text": self._build_prompt()
                            }
                        ],
                    }
                ],
            )

            # Parse response
            response_text = response.choices[0].message.content
            return self._parse_response(response_text)
            
        except (APIConnectionError, ConnectionError) as e:
            logger.error(f"Network error connecting to OpenAI: {str(e)}")
            raise VisionAnalysisError(f"Network error: {str(e)}")
        except RateLimitError:
            logger.warning("Rate limited by OpenAI API")
            raise VisionAnalysisError("Rate limit exceeded. Please try again later.")
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise VisionAnalysisError(f"OpenAI API error: {str(e)}")
    
    def _analyze_gemini(self, image_path: str) -> VisionOutput:
        """Analyze image using Google Gemini"""
        try:
            from PIL import Image
            
            # Load image
            img = Image.open(image_path)
            
            # Build prompt
            prompt = self._build_prompt()
            
            # Call Gemini API
            response = self.client.generate_content([prompt, img])
            
            # Parse response
            response_text = response.text
            return self._parse_response(response_text)
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise VisionAnalysisError(f"Gemini API error: {str(e)}")
    
    def _parse_response(self, response_text: str) -> VisionOutput:
        """Parse and validate vision API response"""
        logger.debug(f"Raw response: {response_text}")
        
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            parsed = json.loads(response_text)
            result = VisionOutput(**parsed)
            logger.info(f"Successfully analyzed image: {len(result.items)} items found")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text}")
            raise VisionAnalysisError(f"Invalid JSON in response: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid response structure: {str(e)}")
            raise VisionAnalysisError(f"Invalid response structure: {str(e)}")

    def _build_prompt(self) -> str:
        """Build the prompt for OpenAI Vision"""
        return """Analyze this pantry shelf image and identify all visible food/pantry items.

Return a JSON response with exactly this structure (no markdown, just raw JSON):
{
  "scene_confidence": 0.0-1.0,
  "items": [
    {
      "name": "item name",
      "brand": "brand or null",
      "package_type": "box|can|jar|bag|bottle|other",
      "quantity_estimate": integer count or null if unclear,
      "confidence": 0.0-1.0
    }
  ],
  "notes": "optional observations about occlusion, lighting, etc"
}

Rules:
- Be specific about item names (e.g., "peanut butter" not "spread")
- Only include items you can see clearly
- Estimate quantity conservatively
- Confidence must reflect visibility and clarity
- If any item is partially hidden, note it in "notes"
"""
