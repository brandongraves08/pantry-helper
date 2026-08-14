# Vision AI Provider Configuration

The Pantry Inventory System analyzes captured images with a configurable vision provider, selected via the `VISION_PROVIDER` env var:

- **Hermes** (default) — agent-driven analysis through an OpenAI-compatible endpoint
- **OpenAI GPT-4 Vision** — direct OpenAI API
- **NVIDIA NIM** — self-hosted or cloud NVIDIA endpoints
- **Ollama** — fully local models (e.g. llava)
- **mock** — no-op for testing

## Quick Configuration

Edit `backend/.env` to choose your provider:

### Option 1: Hermes (default)

```bash
VISION_PROVIDER=hermes
HERMES_VISION_URL=http://localhost:18790/analyze   # optional — agent's OpenAI-compatible endpoint
HERMES_API_KEY=your-key-here
HERMES_MODEL=gpt-4-vision-preview
```

Leave `HERMES_VISION_URL` unset to use the OpenAI API directly with `HERMES_API_KEY`.

### Option 2: OpenAI

```bash
VISION_PROVIDER=openai
OPENAI_API_KEY=your-openai-key-here
OPENAI_MODEL=gpt-4-vision-preview
```

**Get API Key:** https://platform.openai.com/api-keys

### Option 3: NVIDIA NIM

```bash
VISION_PROVIDER=nvidia
NVIDIA_NIM_API_KEY=your-nim-key-here
NVIDIA_MODEL=moonshotai/kimi-k2.5
```

### Option 4: Ollama (local)

```bash
VISION_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llava:latest
```

## Usage

```python
from app.services.vision import VisionAnalyzer

# Auto-detect from VISION_PROVIDER env var
analyzer = VisionAnalyzer()

result = analyzer.analyze_image("pantry_shelf.jpg")
print(f"Found {len(result.items)} items")
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VISION_PROVIDER` | Provider to use (`hermes`, `openai`, `nvidia`, `ollama`, `mock`) | `hermes` |
| `HERMES_VISION_URL` | Hermes agent's OpenAI-compatible vision endpoint | unset (use OpenAI API) |
| `HERMES_API_KEY` | Key for the Hermes/OpenAI endpoint (falls back to `OPENAI_API_KEY`) | - |
| `HERMES_MODEL` | Vision model name | `gpt-4-vision-preview` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model name | `gpt-5` |
| `NVIDIA_NIM_API_KEY` | NVIDIA NIM API key | - |
| `NVIDIA_MODEL` | NVIDIA model name | `moonshotai/kimi-k2.5` |
| `OLLAMA_HOST` | Ollama server | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama vision model | `llava:latest` |

## Switching Providers

1. Edit `backend/.env`
2. Change `VISION_PROVIDER` to your desired provider
3. Set the appropriate key/URL
4. Restart the backend

No code changes required!

## Error Handling

All providers raise `VisionAnalysisError` for failures:

```python
from app.exceptions import VisionAnalysisError

try:
    result = analyzer.analyze_image("image.jpg")
except VisionAnalysisError as e:
    print(f"Analysis failed: {e}")
```

## API Key Security

**Never commit API keys to git!**

```bash
# .env is already in .gitignore
git status  # Should NOT show .env file
```

Use environment variables or secret management in production.
