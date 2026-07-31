#!/usr/bin/env python3
"""Test NVIDIA NIM vision API directly"""
import os
import base64
from openai import OpenAI

# Setup
api_key = os.getenv("NVIDIA_NIM_API_KEY")
model = "meta/llama-3.2-11b-vision-instruct"
image_path = "/home/brandon/.openclaw/media/inbound/531a7eff-7fc4-41ec-8714-aa6185d6f896.jpg"

client = OpenAI(api_key=api_key, base_url="https://integrate.api.nvidia.com/v1")

# Read and encode image
with open(image_path, "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# Build prompt
prompt = """Analyze this pantry shelf image and identify all visible food/pantry items.
Return a JSON response with exactly this structure (no markdown, just raw JSON):
{
  "scene_confidence": 0.0-1.0,
  "items": [
    { "name": "item name", "brand": "brand or null", "package_type": "box|can|jar|bag|bottle|other", "quantity_estimate": integer, "confidence": 0.0-1.0 }
  ],
  "notes": "optional observations"
}"""

try:
    # Test without detail field (may not be supported by Llama)
    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}",
                        },
                    },
                    {"type": "text", "text": prompt}
                ],
            }
        ],
    )
    print("Response received:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
