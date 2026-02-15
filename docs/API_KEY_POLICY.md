# API Key Policy

## Never Hardcode API Keys

**Rule:** All API keys must be loaded from environment variables only.

### Correct Pattern ✅
```python
api_key = os.getenv("OPENROUTER_API_KEY", "")
# or
api_key = os.environ.get("OPENROUTER_API_KEY")
```

### Wrong Pattern ❌
```python
api_key = "sk-or-v1-..."  # NEVER
default="sk-or-v1-..."    # NEVER
```

### Files That Handle Keys
- `src/config.py` - Loads from env vars
- `src/common/openrouter.py` - Loads from config
- `src/common/zai_client.py` - Loads from env vars

### If You Need to Test
1. Use environment variables: `export OPENROUTER_API_KEY="your-key"`
2. Use `.env` file (gitignored)
3. Use placeholders: `sk-or-YOUR-KEY-HERE`

### Git Safety
- `.env` is gitignored
- `.env.example` shows required keys (no values)
- Any committed key = security incident → rotate immediately
