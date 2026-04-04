# LLM Configuration Guide

TailorCv now supports **any LLM provider** — use Anthropic Claude, OpenAI GPT, Google Gemini, or any custom OpenAI-compatible endpoint.

## Supported Providers

### 1. **Anthropic Claude** (Default)

**Setup:**
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

**CLI Usage:**
```bash
# Short form (auto-detects Anthropic)
python main.py --model claude-sonnet-4-6

# Full form with provider prefix
python main.py --model anthropic:claude-sonnet-4-6

# With API key flag (no env variable needed)
python main.py --model anthropic:claude-sonnet-4-6 --api-key "your-key"
```

**Available Models:**
- `anthropic:claude-sonnet-4-6` (default)
- `anthropic:claude-3-5-sonnet-20241022`
- `anthropic:claude-3-opus-20240229`

**Web UI:**
- Select "Anthropic Claude" from provider dropdown
- Model will auto-populate with `anthropic:claude-sonnet-4-6`
- Base URL is automatically set to `https://api.anthropic.com/v1`
- Enter your API key or leave blank if using environment variables

---

### 2. **OpenAI GPT**

**Setup:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

**CLI Usage:**
```bash
# With provider prefix
python main.py --model openai:gpt-4o

# Alternative: use --api-key
python main.py --model openai:gpt-4o --api-key "sk-..."
```

**Available Models:**
- `openai:gpt-4o`
- `openai:gpt-4-turbo`
- `openai:gpt-3.5-turbo`
- `openai:gpt-4`

**Web UI:**
- Select "OpenAI GPT" from provider dropdown
- Model will auto-populate with `openai:gpt-4o`
- Base URL is automatically set to `https://api.openai.com/v1`
- Enter your API key

---

### 3. **Google Gemini**

**Setup:**
```bash
export GOOGLE_API_KEY="your-google-api-key"
```

**CLI Usage:**
```bash
python main.py --model google_genai:gemini-2.5-flash
python main.py --model google_genai:gemini-2.5-pro
python main.py --model google_genai:gemini-flash-latest
```

**Available Models:**
- `google_genai:gemini-2.5-flash` — Latest flash model (fast & cheap) ⚡
- `google_genai:gemini-2.5-pro` — Latest pro model (most capable) 🎯
- `google_genai:gemini-2.5-flash-lite` — Lightweight flash variant
- `google_genai:gemini-flash-latest` — Stable alias (auto-updates)
- `google_genai:gemini-pro-latest` — Stable alias (auto-updates)
- `google_genai:gemini-2.0-flash` — Previous generation

**Web UI:**
- Select "Google Gemini" from provider dropdown
- Model will auto-populate with `google_genai:gemini-2.5-flash`
- Base URL is handled automatically by LangChain (no custom URL needed)
- Enter your API key

---

### 4. **Custom Endpoints** (Azure OpenAI, Local LLMs, Corporate Proxies)

For OpenAI-compatible endpoints like Azure OpenAI, local Ollama servers, corporate proxies, or other custom deployments.

**CLI Usage:**
```bash
# Azure OpenAI
python main.py \
  --model gpt-4 \
  --base-url "https://your-resource.openai.azure.com/openai/deployments/gpt-4/v1" \
  --api-key "your-azure-key"

# Local Ollama
python main.py \
  --model llama3 \
  --base-url http://localhost:11434/v1

# Corporate F5 Proxy
python main.py \
  --model claude-sonnet-4-6 \
  --base-url https://f5ai.pd.f5net.com/api \
  --api-key "your-key"
```

**Web UI:**
- Select "Custom Endpoint" from provider dropdown
- Enter your model name (e.g., `gpt-4`, `llama3`, `claude-sonnet-4-6`)
- Enter the custom API endpoint URL (e.g., `https://your-endpoint.com/v1`)
- Enter your API key if required

**Note:** Custom endpoints must be OpenAI-compatible (support the `/v1/chat/completions` API format).

---

## Standard Provider Base URLs

When using standard providers, base URLs are **automatically handled by LangChain** and should not be specified:

| Provider | Base URL | Configuration |
|----------|----------|---------------|
| **Anthropic** | _(handled automatically)_ | No base URL needed |
| **OpenAI** | _(handled automatically)_ | No base URL needed |
| **Google Gemini** | _(handled automatically)_ | No base URL needed |
| **Custom** | User provided | Required for custom endpoints |

**Important:** Standard provider credentials are managed via API keys only. The base URL field remains empty and hidden in the UI.

---

## Environment Variables vs. CLI Flags

**Priority:** CLI `--api-key` flag > Environment variables

### Environment Variables (Recommended for production):
```bash
export ANTHROPIC_API_KEY="..."
export OPENAI_API_KEY="..."
export GOOGLE_API_KEY="..."
```

### CLI Flags (Quick testing/switching):
```bash
python main.py --model openai:gpt-4o --api-key "sk-..."
```

---

## Web UI Configuration

### Provider Dropdown Options:
1. **Anthropic Claude** — Direct Anthropic API (recommended)
2. **OpenAI GPT** — Direct OpenAI API
3. **Google Gemini** — Direct Google API
4. **Custom Endpoint** — For Azure, proxies, or local LLMs

### Auto-populated Defaults:
When you select a provider, the UI automatically:
- **Fills model name** with recommended default
- **Sets base URL** to the official API endpoint (or shows input for custom)
- **Shows helpful hints** with example model names
- **Hides/shows custom endpoint field** based on selection

### Provider-Specific Behavior:
- **Standard providers (Anthropic/OpenAI/Google):** Base URL is pre-configured and hidden
- **Custom Endpoint:** Shows custom API endpoint input field

---

## Advanced Examples

### CLI: Multi-iteration with custom model
```bash
python main.py \
  --resume data/sample_resume.txt \
  --jd data/sample_jd.txt \
  --model google:gemini-1.5-pro \
  --threshold 90 \
  --max-iterations 5 \
  --instructions "Emphasize Python and distributed systems"
```

### CLI: Using Azure OpenAI
```bash
export OPENAI_API_KEY="your-azure-key"
python main.py \
  --model gpt-4 \
  --base-url "https://your-resource.openai.azure.com/openai/deployments/gpt-4/v1"
```

### Web API: Dynamic model selection
The FastAPI endpoint accepts these parameters:
```python
POST /api/generate
- resume: PDF file
- job_description: str
- model: str (e.g., "openai:gpt-4o")
- base_url: str (optional, for custom endpoints)
- api_key: str (optional)
- threshold: int (80)
- max_iterations: int (10)
```

---

## How It Works Internally

**[src/nodes.py](src/nodes.py)** — `get_llm()` function:

```python
def get_llm(model_name: str, base_url: str = "", api_key: str = ""):
    # 1. Set API key in environment based on provider
    if api_key:
        if "google" in model_name or "gemini" in model_name:
            os.environ["GOOGLE_API_KEY"] = api_key
        elif "anthropic" in model_name or "claude" in model_name:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        else:
            os.environ["OPENAI_API_KEY"] = api_key
    
    # 2. Use custom endpoint if base_url provided
    if base_url:
        return ChatOpenAI(model=model_name, base_url=base_url, temperature=0.3)
    
    # 3. Otherwise, auto-detect provider from model name
    return init_chat_model(model_name, temperature=0.3)
```

**Model Name Format:**
- `provider:model` → Auto-detected by LangChain
- Examples: `anthropic:claude-3`, `openai:gpt-4`, `google:gemini-pro`
- Short names work when provider is obvious: `claude-sonnet-4-6` → Anthropic

---

## Troubleshooting

### Error: "API key not found"
**Solution:** Set the appropriate environment variable or use `--api-key` flag

### Error: "Rate limit exceeded (429)"
**Solution:** The system auto-retries with exponential backoff. Check your API quota.

### Error: "Model not found"
**Solution:** Verify the model name format:
- Include provider prefix: `anthropic:`, `openai:`, `google:`
- Check model availability in your API plan

### Custom endpoint not working
**Solution:**
- Ensure the endpoint is OpenAI-compatible (has `/v1/chat/completions`)
- Use `OPENAI_API_KEY` environment variable for custom endpoints
- Verify base URL format (should end with `/v1`, not `/chat/completions`)

---

## Cost Optimization

**Recommended Models by Use Case:**

| Use Case | Recommended Model | Why |
|----------|------------------|-----|
| **Production** | `anthropic:claude-sonnet-4-6` | Best balance of quality/speed |
| **Cost-conscious** | `google:gemini-1.5-flash` | Cheapest, still excellent |
| **Maximum quality** | `openai:gpt-4o` or `anthropic:claude-3-opus` | Best results |
| **Speed** | `google:gemini-1.5-flash` | Fastest responses |

---

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** in production
3. **Rotate keys regularly**
4. **Use separate keys** for dev/staging/prod
5. **Monitor API usage** to detect anomalies
