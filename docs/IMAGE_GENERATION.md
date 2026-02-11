# Image Generation Setup - G-Manga Pipeline

## Overview

The G-Manga pipeline now supports real image generation via three providers:
1. **DALL-E 3** (OpenAI) - High quality, easy setup
2. **SDXL** (Stability AI) - Open source, cost-effective
3. **OpenRouter** - Multiple models, unified API

## Quick Start

### 1. Set Up API Keys

```bash
# For DALL-E 3 (OpenAI)
export OPENAI_API_KEY="sk-your-openai-key"

# For SDXL (Stability AI)  
export STABILITY_API_KEY="sk-your-stability-key"

# For OpenRouter (supports multiple SD models)
export OPENROUTER_API_KEY="sk-or-your-openrouter-key"
```

Or add them to your `config.yaml`:
```yaml
image:
  dalle:
    api_key_env: "OPENAI_API_KEY"
  sdxl:
    api_key_env: "STABILITY_API_KEY"
  openrouter:
    api_key_env: "OPENROUTER_API_KEY"
```

### 2. Test the Setup

```bash
cd /home/clawd/projects/g-manga
python3 test_image_generation_setup.py
```

### 3. Generate Images

```python
from stage6_image_generation.providers import create_image_provider

# Create provider
provider = create_image_provider(
    provider_type="dalle3",
    api_key="sk-your-key"  # Or set via env var
)

# Generate image
result = provider.generate(
    prompt="A manga panel showing a dramatic fight scene",
    size=ImageSize.SQUARE_1024,
    quality=ImageQuality.HD
)

if result.success:
    with open("output.png", "wb") as f:
        f.write(result.image_bytes)
    print(f"Image saved! Cost: ${result.cost:.2f}")
else:
    print(f"Generation failed: {result.error}")
```

## Provider Comparison

| Provider | Cost/Image | Quality | Setup Difficulty |
|----------|-----------|---------|-----------------|
| DALL-E 3 | $0.04-0.12 | Excellent | Easy |
| SDXL | $0.04 | Very Good | Medium |
| OpenRouter | $0.01-0.10 | Varies | Easy |

## Configuration

### DALL-E 3 Settings

```yaml
image:
  dalle:
    enabled: true
    model: "dall-e-3"
    size: "1024x1024"  # or "1792x1024", "1024x1792"
    quality: "hd"      # or "standard"
    style: "vivid"     # or "natural"
    rate_limit: 10     # requests per minute
    timeout: 60        # seconds
    max_retries: 3
```

### SDXL Settings

```yaml
image:
  sdxl:
    enabled: true
    model: "stable-diffusion-xl-1024-v1-0"
    size: "1024x1024"
    steps: 30          # diffusion steps (20-50)
    cfg_scale: 7.5     # guidance scale (1-20)
    rate_limit: 20
    timeout: 60
    max_retries: 3
```

### OpenRouter Settings

```yaml
image:
  openrouter:
    enabled: true
    default_model: "stabilityai/stable-diffusion-xl-base-1.0"
    available_models:
      - "stabilityai/stable-diffusion-xl-base-1.0"
      - "stabilityai/stable-diffusion-xl-refiner-1.0"
      - "runwayml/stable-diffusion-v1-5"
    size: "1024x1024"
    rate_limit: 20
    timeout: 60
    max_retries: 3
```

## API Keys

### Getting API Keys

**OpenAI (DALL-E 3):**
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add billing method (pay-per-use)

**Stability AI (SDXL):**
1. Go to https://platform.stability.ai/
2. Sign up and get API key
3. Check pricing on their website

**OpenRouter:**
1. Go to https://openrouter.ai/keys
2. Create a free account
3. Get API key (includes free credits)

### Security Notes

- **Never commit API keys** to version control
- Use **environment variables** or **.env files**
- Consider using a ** secrets manager** for production
- Set up **usage limits** on your API provider dashboards

## Usage Examples

### Basic Image Generation

```python
from stage6_image_generation.providers import create_image_provider

# Create DALL-E 3 provider
provider = create_image_provider("dalle3")

# Generate manga panel
result = provider.generate(
    prompt="Anime-style character with spiky blue hair, dramatic pose, action scene",
    size=ImageSize.SQUARE_1024,
    quality=ImageQuality.HD
)

if result.success:
    print(f"Generated! Cost: ${result.cost:.2f}")
```

### Batch Generation

```python
prompts = [
    "Manga panel: heroic character charging forward",
    "Manga panel: intense dialogue scene",
    "Manga panel: dramatic reveal",
]

results = provider.batch_generate(
    prompts=prompts,
    size=ImageSize.SQUARE_1024,
    quality=ImageQuality.HD
)

print(f"Success: {results.total_success}/{results.total_requested}")
print(f"Total cost: ${results.total_cost:.2f}")
```

### Using Different Providers

```python
# DALL-E 3 (best quality)
dalle = create_image_provider("dalle3", api_key="...")

# SDXL (cheapest)
sdxl = create_image_provider("sdxl", api_key="...")

# OpenRouter (most flexible)
orouter = create_image_provider(
    "openrouter", 
    api_key="...",
    model="runwayml/stable-diffusion-v1-5"
)
```

### Cost Estimation

```python
# Estimate cost before generating
provider = create_image_provider("dalle3")

cost = provider.estimate_cost(
    num_images=4,
    size=ImageSize.SQUARE_1024,
    quality=ImageQuality.HD
)
print(f"4 HD images will cost: ${cost:.2f}")
```

### Validation

```python
# Validate generated images
result = provider.generate(prompt="...")
if result.success:
    validation = provider.validate(result.image_bytes, result.prompt)
    print(f"Image score: {validation.score:.2f}")
    if not validation.is_valid:
        for error in validation.errors:
            print(f"Error: {error.error_message}")
```

## Troubleshooting

### Rate Limit Errors

```
Error: Rate limit exceeded: X requests in last 60 seconds
```

**Solution:** Reduce request frequency or increase rate_limit in config.

### Authentication Errors

```
Error: Invalid API key
```

**Solution:** 
1. Check your API key is correct
2. Verify the environment variable is set
3. Check API provider dashboard for key status

### Timeout Errors

```
Error: Request timeout after 60 seconds
```

**Solution:** 
1. Increase timeout in config
2. Reduce image size or quality
3. Check your internet connection

### Generation Failures

```
Error: API error: content moderation
```

**Solution:** 
1. Modify the prompt to be less explicit
2. Remove sensitive content from prompt
3. Try a different provider

## Advanced Usage

### Custom Provider Configuration

```python
from stage6_image_generation.providers import ProviderConfig

config = ProviderConfig(
    provider_type=ProviderType.DALLE3,
    api_key="your-key",
    max_retries=5,
    timeout=120,
    rate_limit=5,  # More conservative rate limit
    quality=ImageQuality.HD,
    default_size=ImageSize.LANDSCAPE_1792
)

provider = ImageProviderFactory.create_from_config(config)
```

### Switching Providers Based on Cost

```python
from stage6_image_generation.providers import create_image_provider

# Choose cheapest provider for batch generation
providers = [
    ("dalle3", 0.04),
    ("sdxl", 0.04),
    ("openrouter", 0.01),
]

cheapest = min(providers, key=lambda x: x[1])
provider = create_image_provider(cheapest[0])
```

## File Structure

```
g-manga/
├── config.yaml                          # Main configuration
├── src/
│   ├── config.py                        # Settings classes
│   └── stage6_image_generation/
│       └── providers/
│           ├── __init__.py             # Exports all providers
│           ├── base.py                 # Base classes
│           ├── dalle.py                # DALL-E 3 implementation
│           ├── sdxl.py                # SDXL implementation
│           ├── openrouter.py          # OpenRouter implementation
│           └── factory.py             # Provider factory
└── test_image_generation_setup.py      # Setup test
```

## Next Steps

1. **Set up API keys** for your chosen provider(s)
2. **Test with real generation**: `python3 test_image_generation_setup.py`
3. **Integrate into pipeline**: Use `create_image_provider()` in your code
4. **Monitor costs**: Track usage in your API provider dashboards
5. **Set up alerts**: Configure usage limits and notifications

## Support

- Check provider documentation:
  - [OpenAI DALL-E 3](https://platform.openai.com/docs/guides/images)
  - [Stability AI](https://platform.stability.ai/docs/getting-started)
  - [OpenRouter](https://openrouter.ai/docs)

- Report issues to the G-Manga repository
