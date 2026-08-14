# Vision AI Provider Configuration

The Pantry Inventory System supports several Vision AI providers for image analysis, selected via the `VISION_PROVIDER` env var:

- **OpenClaw gateway** (default) — routes to a model of your choice through a local gateway
- **OpenAI GPT-4 Vision** — direct OpenAI API
- **NVIDIA NIM** — self-hosted or cloud NVIDIA endpoints
- **Ollama** — fully local models (e.g. llava)
- **mock** — no-op for testing

## Quick Configuration

Edit `backend/.env` to choose your provider:

### Option 1: OpenClaw gateway (default)

```bash
VISION_PROVIDER=openclaw
OPENCLAW_VISION_URL=http://localhost:18790/analyze
OPENCLAW_GATEWAY_TOKEN=your-gateway-token
OPENCLAW_VISION_MODEL=openai/gpt-4o-mini
```

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
| `VISION_PROVIDER` | Provider to use (`openclaw`, `openai`, `nvidia`, `ollama`, `mock`) | `openclaw` |
| `OPENCLAW_VISION_URL` | OpenClaw gateway URL | `http://localhost:18790/analyze` |
| `OPENCLAW_GATEWAY_TOKEN` | OpenClaw gateway token (or `OPENCLAW_GATEWAY_TOKEN_FILE`) | - |
| `OPENCLAW_VISION_MODEL` | Model routed through the gateway | `openai/gpt-5.4-mini` |
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
