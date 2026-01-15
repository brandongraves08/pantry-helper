import base64
import json
import logging
from typing import Optional
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from app.models.schemas import VisionOutput
from app.exceptions import VisionAnalysisError

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """Handles OpenAI Vision API calls for pantry image analysis"""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4-vision-preview"
        self.max_retries = 3

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
        try:
            logger.info(f"Analyzing image: {image_path}")
            
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

            # Parse response as JSON
            response_text = response.choices[0].message.content
            logger.debug(f"Raw response: {response_text}")
            
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
                
        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            raise VisionAnalysisError(f"Image file not found: {image_path}")
        except (APIConnectionError, ConnectionError) as e:
            logger.error(f"Network error connecting to OpenAI: {str(e)}")
            raise VisionAnalysisError(f"Network error: {str(e)}")
        except RateLimitError:
            logger.warning("Rate limited by OpenAI API")
            raise VisionAnalysisError("Rate limit exceeded. Please try again later.")
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise VisionAnalysisError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error during image analysis: {str(e)}")
            raise VisionAnalysisError(f"Unexpected error: {str(e)}")

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
