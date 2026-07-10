"""Multi-provider vision analysis with structured logging."""
import base64
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Optional
from app.models.schemas import VisionOutput
from app.exceptions import VisionAnalysisError

logger = logging.getLogger("pantry-worker.vision")


class VisionAnalyzer:
    """Multi-provider vision API handler for pantry image analysis."""

    def __init__(self, api_key: str = None, provider: str = None):
        self.provider = provider or os.getenv("VISION_PROVIDER", "openai").lower()
        self.api_key = api_key or self._get_api_key()
        self.max_retries = 3

        logger.info("Initializing vision analyzer", extra={"provider": self.provider})

        if self.provider in ("openclaw", "openclaw-gateway"):
            self._init_openclaw()
        elif self.provider == "openai":
            self._init_openai()
        elif self.provider == "nvidia":
            self._init_nvidia()
        elif self.provider == "ollama":
            self._init_ollama()
        elif self.provider in ("mock", "none"):
            self._init_mock()
        else:
            raise ValueError(f"Unsupported vision provider: {self.provider}")

    def _get_api_key(self) -> str:
        if self.provider in ("openclaw", "openclaw-gateway"):
            key = os.getenv("OPENCLAW_GATEWAY_TOKEN")
            token_file = os.getenv("OPENCLAW_GATEWAY_TOKEN_FILE")
            if not key and token_file:
                try:
                    with open(token_file, "r", encoding="utf-8") as f:
                        key = f.read().strip()
                except OSError as e:
                    raise ValueError(f"OPENCLAW_GATEWAY_TOKEN_FILE is unreadable: {e}")
            if not key:
                raise ValueError("OPENCLAW_GATEWAY_TOKEN or OPENCLAW_GATEWAY_TOKEN_FILE is required for OpenClaw provider")
            return key
        if self.provider == "openai":
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            return key
        if self.provider == "nvidia":
            key = os.getenv("NVIDIA_NIM_API_KEY")
            if not key:
                raise ValueError("NVIDIA_NIM_API_KEY is required for NVIDIA provider")
            return key
        return ""

    def _init_openclaw(self):
        self.vision_url = os.getenv(
            "OPENCLAW_VISION_URL",
            "http://172.16.1.1:18790/analyze",
        )
        self.model = os.getenv("OPENCLAW_VISION_MODEL", "openai/gpt-5.4-mini")
        logger.info("OpenClaw vision provider initialized", extra={
            "model": self.model,
            "vision_url": self.vision_url,
        })

    def _init_openai(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-5")
            logger.info("OpenAI client initialized", extra={"model": self.model})
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def _init_nvidia(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("NVIDIA_NIM_API_KEY"),
                base_url="https://integrate.api.nvidia.com/v1",
            )
            self.model = os.getenv("NVIDIA_MODEL", "moonshotai/kimi-k2.5")
            logger.info("NVIDIA NIM client initialized", extra={"model": self.model})
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def _init_mock(self):
        self.client = None
        self.model = "mock"
        logger.info("Mock vision provider initialized (no-op)")

    def analyze_image(self, image_path: str) -> VisionOutput:
        logger.info("Analyzing image", extra={
            "provider": self.provider,
            "image_path": image_path,
        })
        try:
            if self.provider in ("openclaw", "openclaw-gateway"):
                return self._analyze_openclaw(image_path)
            if self.provider == "openai":
                return self._analyze_openai(image_path)
            if self.provider == "nvidia":
                return self._analyze_nvidia(image_path)
            if self.provider == "ollama":
                return self._analyze_ollama(image_path)
            if self.provider in ("mock", "none"):
                with open(image_path, "rb"):
                    pass
                logger.info("Mock analysis (no-op)")
                return VisionOutput(scene_confidence=0.0, items=[], notes="mock provider: no analysis performed")
        except FileNotFoundError:
            logger.error("Image file not found", extra={"path": image_path})
            raise VisionAnalysisError(f"Image file not found: {image_path}")
        except Exception as e:
            logger.exception("Unexpected analysis error", extra={"error": str(e)})
            raise VisionAnalysisError(f"Unexpected error: {str(e)}")

    def _analyze_openclaw(self, image_path: str) -> VisionOutput:
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            payload = {"model": self.model, "image_base64": image_data, "prompt": self._build_prompt()}
            req = urllib.request.Request(
                self.vision_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=int(os.getenv("OPENCLAW_TIMEOUT", "120"))) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            response_text = result["text"]
            logger.info("OpenClaw vision response received", extra={"model": result.get("model")})
            return self._parse_response(response_text)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            logger.error("OpenClaw vision HTTP error", extra={"status": e.code, "body": body})
            raise VisionAnalysisError(f"OpenClaw vision HTTP error {e.code}: {body}")
        except urllib.error.URLError as e:
            logger.error("OpenClaw vision network error", extra={"error": str(e)})
            raise VisionAnalysisError(f"OpenClaw vision network error: {str(e)}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error("OpenClaw vision response parse error", extra={"error": str(e)})
            raise VisionAnalysisError(f"OpenClaw vision response parse error: {str(e)}")

    def _analyze_openai(self, image_path: str) -> VisionOutput:
        from openai import APIError, APIConnectionError, RateLimitError
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}", "detail": "high"}},
                            {"type": "text", "text": self._build_prompt()}
                        ],
                    }
                ],
            )
            response_text = response.choices[0].message.content
            logger.info("OpenAI response received", extra={"tokens": response.usage.total_tokens if hasattr(response, 'usage') and response.usage else None})
            return self._parse_response(response_text)
        except (APIConnectionError, ConnectionError) as e:
            logger.error("OpenAI network error", extra={"error": str(e)})
            raise VisionAnalysisError(f"Network error: {str(e)}")
        except RateLimitError:
            logger.warning("OpenAI rate limit hit")
            raise VisionAnalysisError("Rate limit exceeded. Please try again later.")
        except APIError as e:
            logger.error("OpenAI API error", extra={"error": str(e), "status": e.status_code if hasattr(e, 'status_code') else None})
            raise VisionAnalysisError(f"OpenAI API error: {str(e)}")

    def _analyze_nvidia(self, image_path: str) -> VisionOutput:
        from openai import APIError, APIConnectionError, RateLimitError
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}", "detail": "high"}},
                            {"type": "text", "text": self._build_prompt()}
                        ],
                    }
                ],
            )
            response_text = response.choices[0].message.content
            logger.info("NVIDIA response received")
            return self._parse_response(response_text)
        except (APIConnectionError, ConnectionError) as e:
            logger.error("NVIDIA network error", extra={"error": str(e)})
            raise VisionAnalysisError(f"Network error: {str(e)}")
        except RateLimitError:
            logger.warning("NVIDIA rate limit hit")
            raise VisionAnalysisError("Rate limit exceeded.")
        except APIError as e:
            logger.error("NVIDIA API error", extra={"error": str(e)})
            raise VisionAnalysisError(f"NVIDIA API error: {str(e)}")

    def _init_ollama(self):
        import requests
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llava:latest")
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info("Ollama connected", extra={"model": self.model, "host": self.ollama_host})
        except Exception as e:
            logger.warning("Ollama connection test failed", extra={"error": str(e)})

    def _analyze_ollama(self, image_path: str) -> VisionOutput:
        import requests
        try:
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode("utf-8")
            prompt = self._build_prompt()
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={"model": self.model, "prompt": prompt, "images": [image_base64], "stream": False},
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            response_text = result.get("response", "")
            return self._parse_response(response_text)
        except requests.exceptions.ConnectionError as e:
            logger.error("Ollama connection failed", extra={"host": self.ollama_host})
            raise VisionAnalysisError(f"Ollama not running. Start with: ollama serve")
        except Exception as e:
            logger.error("Ollama error", extra={"error": str(e)})
            raise VisionAnalysisError(f"Ollama error: {str(e)}")

    def _parse_response(self, response_text: str) -> VisionOutput:
        if not response_text or not response_text.strip():
            logger.warning("Empty response from vision API")
            raise VisionAnalysisError("Empty response from vision API")
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        try:
            parsed = json.loads(response_text)
            result = VisionOutput(**parsed)
            logger.info("Parsed vision result", extra={"items": len(result.items)})
            return result
        except json.JSONDecodeError:
            logger.warning("JSON parse failed, fallback to text extraction", extra={"response_preview": response_text[:800]})
            return self._extract_items_from_text(response_text)
        except ValueError as e:
            logger.error("Invalid response structure", extra={"error": str(e)})
            raise VisionAnalysisError(f"Invalid response structure: {str(e)}")

    def _extract_items_from_text(self, text: str) -> VisionOutput:
        import re
        items = []
        # Try to find items from a malformed JSON-like response
        json_items = re.findall(r'"name"\s*:\s*"([^"]+)"', text)
        if json_items:
            for name in json_items:
                n = name.strip()
                if n and len(n) > 2 and len(n.split()) <= 5:
                    items.append({"name": n, "brand": None, "package_type": "other", "quantity_estimate": None, "confidence": 0.5})
        patterns = [r'(?:^|\n)[-*]\s*([A-Za-z][^:\n]{2,60})', r'(?:^|\n)\d+\.{0,1}\s*([A-Za-z][^:\n]{2,60})']
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.strip()
                if name and len(name) > 2 and len(name.split()) <= 5:
                    lower = name.lower()
                    skip_words = ['with', 'and', 'are', 'the', 'this', 'that', 'from', 'various']
                    word_count = len(name.split())
                    skip_count = sum(1 for w in skip_words if w in lower)
                    if word_count > 3 and skip_count >= max(1, word_count // 2):
                        continue
                    if lower not in ('cans', 'boxes', 'jars', 'items', 'assortment', 'display', 'selection', 'variety', 'arrangement', 'section', 'produce'):
                        items.append({"name": name, "brand": None, "package_type": "other", "quantity_estimate": None, "confidence": 0.5})
        seen = set()
        unique_items = []
        for item in items:
            if item["name"].lower() not in seen:
                seen.add(item["name"].lower())
                unique_items.append(item)
        logger.info("Text-extracted items", extra={"count": len(unique_items)})
        return VisionOutput(
            scene_confidence=0.5 if unique_items else 0.3,
            items=unique_items,
            notes=f"Text-only response. Full response: {text[:200]}..."
        )

    def _build_prompt(self) -> str:
        return """You are a pantry inventory vision system. Analyze the image and identify all visible food/pantry items.

You MUST respond with ONLY valid JSON. No markdown, no code fences, no explanation, no greeting.

Return exactly this JSON structure:
{
  "scene_confidence": 0.0-1.0,
  "items": [
    {
      "name": "specific item name (e.g. 'peanut butter', not 'spread')",
      "brand": "brand name or null",
      "package_type": "box" or "can" or "jar" or "bag" or "bottle" or "other",
      "quantity_estimate": integer count of this item visible, or null if unclear,
      "confidence": 0.0-1.0 reflecting visibility clarity
    }
  ],
  "notes": "optional observations"
}

Rules:
- Be specific: 'creamy peanut butter' not 'spread'
- Only list items you can clearly identify
- Estimate quantity conservatively
- Items partially hidden should have lower confidence
- If you cannot identify any items, return {"scene_confidence": 0, "items": [], "notes": "no identifiable items"}"""
