# Vision AI Provider Configuration

The Pantry Inventory System supports multiple Vision AI providers for image analysis:

- **OpenAI GPT-4 Vision** (default)
- **Google Gemini 1.5**

## Quick Configuration

Edit `backend/.env` to choose your provider:

### Option 1: OpenAI (Default)

```bash
VISION_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4-vision-preview
```

**Get API Key:** https://platform.openai.com/api-keys

### Option 2: Google Gemini

```bash
VISION_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key-here
GEMINI_MODEL=gemini-1.5-flash
```

**Get API Key:** https://makersuite.google.com/app/apikey

## Provider Comparison

| Feature | OpenAI GPT-4 Vision | Google Gemini 1.5 |
|---------|-------------------|-------------------|
| **Accuracy** | Excellent | Excellent |
| **Speed** | ~2-5 seconds | ~1-3 seconds |
| **Cost** | $0.01 per image | Free (with limits) |
| **Rate Limits** | 500 RPM | 60 RPM (free tier) |
| **Image Size** | 20MB max | 20MB max |
| **Formats** | JPEG, PNG, WebP | JPEG, PNG, WebP, GIF |

## Usage Examples

### Using OpenAI

```python
from app.services.vision import VisionAnalyzer

# Explicit provider
analyzer = VisionAnalyzer(
    api_key="sk-...",
    provider="openai"
)

# Auto-detect from environment
analyzer = VisionAnalyzer()  # Uses VISION_PROVIDER env var

result = analyzer.analyze_image("pantry_shelf.jpg")
print(f"Found {len(result.items)} items")
```

### Using Gemini

```python
from app.services.vision import VisionAnalyzer

analyzer = VisionAnalyzer(
    api_key="your-gemini-key",
    provider="gemini"
)

result = analyzer.analyze_image("pantry_shelf.jpg")
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VISION_PROVIDER` | Provider to use (`openai` or `gemini`) | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4-vision-preview` |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `GEMINI_MODEL` | Gemini model name | `gemini-1.5-flash` |

## Switching Providers

1. Edit `backend/.env`
2. Change `VISION_PROVIDER` to your desired provider
3. Set the appropriate API key
4. Restart the backend: `make backend-run`

No code changes required!

## Error Handling

Both providers raise `VisionAnalysisError` for failures:

```python
from app.exceptions import VisionAnalysisError

try:
    result = analyzer.analyze_image("image.jpg")
except VisionAnalysisError as e:
    print(f"Analysis failed: {e}")
```

## Testing

Test with different providers:

```bash
# Test with OpenAI
VISION_PROVIDER=openai python demo.py

# Test with Gemini
VISION_PROVIDER=gemini python demo.py
```

## Production Recommendations

### For High Accuracy
Use **OpenAI GPT-4 Vision** - better at:
- Complex scenes with occlusion
- Brand recognition
- Quantity estimation

### For Cost Efficiency
Use **Google Gemini** - better for:
- High volume processing
- Budget constraints
- Faster response times

### Hybrid Approach
Use both providers with fallback:

```python
def analyze_with_fallback(image_path):
    try:
        # Try primary provider
        analyzer = VisionAnalyzer(provider="openai")
        return analyzer.analyze_image(image_path)
    except VisionAnalysisError:
        # Fallback to secondary
        analyzer = VisionAnalyzer(provider="gemini")
        return analyzer.analyze_image(image_path)
```

## Troubleshooting

### "OPENAI_API_KEY is required"
- Set `OPENAI_API_KEY` in `backend/.env`
- Or switch to Gemini: `VISION_PROVIDER=gemini`

### "google-generativeai package not installed"
```bash
pip install google-generativeai
```

### "Rate limit exceeded"
- OpenAI: Upgrade your plan or reduce request rate
- Gemini: Wait or upgrade to paid tier

### "Invalid API key"
- Verify key is correct in `.env`
- Check key hasn't expired
- Ensure key has vision API access

## Cost Estimation

### OpenAI Pricing
- Input: $0.01 per image (high detail)
- ~100 images = $1.00
- ~1000 images/day = $30/month

### Gemini Pricing
- Free tier: 60 requests/minute
- Paid tier: Higher limits, similar pricing to OpenAI
- Great for prototyping and low-volume use

## API Key Security

**Never commit API keys to git!**

```bash
# .env is already in .gitignore
git status  # Should NOT show .env file
```

Use environment variables or secret management in production.
