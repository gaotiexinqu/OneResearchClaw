#!/usr/bin/env python3
"""
Standalone External Reviewer API Caller

Direct API caller for grounded-review external reviewer scoring.
Supports OpenAI-compatible APIs and Gemini APIs.

Usage:
    python call_ext_api.py --provider openai --model gpt-4o-mini \
        --api-key "sk-xxx" --base-url "https://api.example.com/v1" \
        --system-prompt "You are a reviewer..." \
        --user-prompt "Review this report..." \
        --temperature 0.2 --max-tokens 4096
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    print(json.dumps({"error": "requests library required. Install with: pip install requests"}))
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


DEFAULT_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "gemini": "https://modelservice.jdcloud.com/v1/responses",
}


def call_openai_api(
    model: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Call OpenAI-compatible API using the official OpenAI SDK."""
    if OpenAI is None:
        raise ImportError("openai library required. Install with: pip install openai")

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url.rstrip("/")

    client = OpenAI(**client_kwargs)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    choice = completion.choices[0].message
    content = choice.content or ""

    result = {"content": content}

    if completion.usage:
        usage = completion.usage
        if hasattr(usage, "model_dump"):
            result["usage"] = usage.model_dump()
        elif hasattr(usage, "dict"):
            result["usage"] = usage.dict()
        else:
            result["usage"] = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            }

    return result


def call_gemini_api(
    model: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Call Gemini API (JD Cloud format or Google format)."""
    base = base_url or DEFAULT_ENDPOINTS["gemini"]
    base = base.rstrip("/")

    if "jdcloud" in base:
        url = f"{base}/responses"
        combined_content = f"{system_prompt}\n\n---\n\n{user_prompt}"
        payload = {
            "model": model,
            "stream": False,
            "contents": {
                "role": "user",
                "parts": [{"text": combined_content}]
            },
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
                "maxOutputTokens": max_tokens,
            }
        }
    else:
        url = f"{base}/{model}:generateContent"
        combined_content = f"{system_prompt}\n\n---\n\n{user_prompt}"
        payload = {
            "contents": {
                "role": "user",
                "parts": [{"text": combined_content}]
            },
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120,
        proxies={"http": None, "https": None},
    )

    response.raise_for_status()
    data = response.json()

    content = ""
    if "candidates" in data:
        candidate = data["candidates"][0]
        if "content" in candidate:
            parts = candidate["content"].get("parts", [])
            for part in parts:
                if isinstance(part, dict) and "text" in part:
                    content += part["text"]

    usage_info = {}
    if "usageMetadata" in data:
        um = data["usageMetadata"]
        usage_info = {
            "prompt_tokens": um.get("promptTokenCount", 0),
            "completion_tokens": um.get("candidatesTokenCount", 0),
            "total_tokens": um.get("totalTokenCount", 0),
        }

    result = {"content": content}
    if usage_info:
        result["usage"] = usage_info

    return result


def call_ext_reviewer(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    api_key_env: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    system_prompt: str = "",
    user_prompt: str = "",
) -> Dict[str, Any]:
    """Call external reviewer API."""
    if api_key:
        resolved_key = api_key
    elif api_key_env:
        import os
        resolved_key = os.environ.get(api_key_env, "")
        if not resolved_key:
            return {"error": f"API key not found in environment variable: {api_key_env}", "status": "failed"}
    else:
        return {"error": "Either 'api_key' or 'api_key_env' must be provided", "status": "failed"}

    try:
        if provider == "openai":
            result = call_openai_api(
                model=model,
                api_key=resolved_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                base_url=base_url,
            )
        elif provider == "gemini":
            result = call_gemini_api(
                model=model,
                api_key=resolved_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                base_url=base_url,
            )
        else:
            return {"error": f"Unknown provider: {provider}. Supported: openai, gemini", "status": "failed"}

        return result

    except Exception as e:
        return {"error": str(e), "status": "failed"}


def main():
    parser = argparse.ArgumentParser(description="Call external reviewer API")
    parser.add_argument("--provider", required=True, choices=["openai", "gemini"], help="API provider")
    parser.add_argument("--model", required=True, help="Model name")
    parser.add_argument("--api-key", help="API key (use --api-key-env as alternative)")
    parser.add_argument("--api-key-env", help="Environment variable name containing API key")
    parser.add_argument("--base-url", help="Base URL for the API")
    parser.add_argument("--temperature", type=float, default=0.3, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Maximum tokens to generate")
    parser.add_argument("--system-prompt", required=True, help="System prompt")
    parser.add_argument("--user-prompt", required=True, help="User prompt")
    parser.add_argument("--output", help="Output JSON file path (optional)")

    args = parser.parse_args()

    result = call_ext_reviewer(
        provider=args.provider,
        model=args.model,
        api_key=args.api_key,
        api_key_env=args.api_key_env,
        base_url=args.base_url,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        system_prompt=args.system_prompt,
        user_prompt=args.user_prompt,
    )

    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(json.dumps({"status": "success", "output_file": args.output}, ensure_ascii=False, indent=2))
    else:
        print(output)


if __name__ == "__main__":
    main()
