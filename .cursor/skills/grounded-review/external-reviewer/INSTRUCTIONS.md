# External Reviewer MCP Server

Call external LLM APIs as the reviewer for grounded-review scoring. Supports OpenAI-compatible APIs and Gemini APIs.

## Purpose

When using the one-report skill, you can specify an external LLM API via `reviewer_api_config` to perform review scoring, instead of using the local Cursor reviewer subagent.

## Authentication

### Method 1: Direct API Key

```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "api_key": "sk-xxxxx",
  "system_prompt": "...",
  "user_prompt": "..."
}
```

### Method 2: Environment Variable

```json
{
  "provider": "gemini",
  "model": "Gemini-3-Flash-Preview",
  "api_key_env": "GEMINI_API_KEY",
  "system_prompt": "...",
  "user_prompt": "..."
}
```

## Supported Providers

### OpenAI Compatible API

Suitable for:
- Official OpenAI API
- Third-party proxies/custom endpoints (e.g., vLLM, local models, third-party API services)

**Example Config (Official OpenAI)**:
```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "api_key_env": "OPENAI_API_KEY",
  "temperature": 0.2,
  "max_tokens": 4096
}
```

**Example Config (Third-party Proxy)**:
```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "api_key": "sk-xxxxx",
  "base_url": "https://api.gptplus5.com/v1",
  "temperature": 0.2
}
```

### Gemini API (JD Cloud / Google Format)

Suitable for:
- JD Cloud Gemini service
- Google Gemini API

**Note**: Gemini uses a special request format (`contents` as a dict instead of messages array).

**Example Config (JD Cloud)**:
```json
{
  "provider": "gemini",
  "model": "Gemini-3-Flash-Preview",
  "api_key_env": "GEMINI_API_KEY",
  "base_url": "https://modelservice.jdcloud.com/v1",
  "temperature": 0.2
}
```

**Example Config (Google Gemini)**:
```json
{
  "provider": "gemini",
  "model": "gemini-2.5-pro-preview-03-12",
  "api_key_env": "GOOGLE_API_KEY",
  "temperature": 0.2
}
```

## Response Format

Success returns JSON:
```json
{
  "content": "Model's response text...",
  "usage": {
    "prompt_tokens": 1000,
    "completion_tokens": 500,
    "total_tokens": 1500
  }
}
```

Failure returns JSON:
```json
{
  "error": "Error message",
  "status": "failed"
}
```

## Usage in one-report

```text
Use the one-report skill to generate a report.

Input:
- input_path: data/raw_inputs/meeting.pdf
- output_formats: md

Reviewer:
- provider: openai
- model: gpt-4o
- api_key_env: OPENAI_API_KEY
- temperature: 0.2
```

## Dependencies

- Python 3.8+
- `requests` library (for Gemini API)
- `openai` library (for OpenAI-compatible API)

Install dependencies:
```bash
pip install requests openai
```

## Comparison: External vs Local Reviewer

| Aspect | External Reviewer (MCP) | Local Reviewer (Task) |
|--------|-------------------------|----------------------|
| Invocation | MCP tool call | Task tool + Subagent |
| Model | Fully customizable | Limited to Cursor models |
| Cost | Use cheaper models | Uses Cursor subscription |
| Config | Via api_key_env | Via reviewer.md |
| Use Case | Precise model/cost control | Quick default setup |

## Notes

1. **Temperature**: Recommended 0.1-0.3. Higher temperature may cause unstable scoring.
2. **Token Limit**: Adjust `max_tokens` based on report length. Minimum 4096 recommended.
3. **API Key Security**: Prefer `api_key_env` method to avoid hardcoding keys.
4. **Network Latency**: External API calls have network latency. Set reasonable timeout.
5. **Fallback**: If external API fails, you can fall back to local Cursor reviewer.
