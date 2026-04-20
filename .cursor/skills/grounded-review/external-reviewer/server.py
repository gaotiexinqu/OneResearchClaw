#!/usr/bin/env python3
"""
External Reviewer MCP Server

MCP-compliant server that calls external LLM APIs for grounded-review scoring.
Supports OpenAI-compatible APIs and Gemini APIs.

Protocol: MCP over stdio (JSON-RPC 2.0)
"""

import json
import os
import sys
import uuid
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    raise ImportError("requests library is required. Install with: pip install requests")

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ============================================================================
# API Provider Endpoints
# ============================================================================

DEFAULT_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "gemini": "https://modelservice.jdcloud.com/v1/responses",
}


# ============================================================================
# OpenAI Compatible API Caller
# ============================================================================

def call_openai_api(
    model: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call OpenAI-compatible API using the official OpenAI SDK.
    """
    if OpenAI is None:
        raise ImportError("openai library is required. Install with: pip install openai")
    
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


# ============================================================================
# Gemini API Caller (JD Cloud / Google Format)
# ============================================================================

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
    
    # JD Cloud uses /v1/responses endpoint
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
        # Google Gemini format
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
        "Trace-Id": str(uuid.uuid4()),
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
                # Get text content, skip thoughtSignature
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


# ============================================================================
# Main MCP Tool Handler
# ============================================================================

def call_ext_reviewer(
    provider: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    api_key: Optional[str] = None,
    api_key_env: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """
    Main MCP tool handler for calling external reviewer APIs.
    
    Returns JSON string with the API response (content and usage).
    """
    # Resolve API key
    if api_key:
        resolved_key = api_key
    elif api_key_env:
        resolved_key = os.environ.get(api_key_env, "")
        if not resolved_key:
            return json.dumps({
                "error": f"API key not found in environment variable: {api_key_env}",
                "status": "failed"
            }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({
            "error": "Either 'api_key' or 'api_key_env' must be provided",
            "status": "failed"
        }, ensure_ascii=False, indent=2)
    
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
            return json.dumps({
                "error": f"Unknown provider: {provider}. Supported: openai, gemini",
                "status": "failed"
            }, ensure_ascii=False, indent=2)
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "status": "failed"
        }, ensure_ascii=False, indent=2)


# ============================================================================
# Tool Definitions (MCP Schema)
# ============================================================================

TOOLS = [
    {
        "name": "call_ext_reviewer",
        "description": "Call external LLM APIs as the reviewer for grounded-review scoring.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "enum": ["openai", "gemini"]},
                "model": {"type": "string"},
                "api_key": {"type": "string"},
                "api_key_env": {"type": "string"},
                "base_url": {"type": "string"},
                "temperature": {"type": "number", "default": 0.3},
                "max_tokens": {"type": "number", "default": 4096},
                "system_prompt": {"type": "string"},
                "user_prompt": {"type": "string"}
            },
            "required": ["provider", "model", "system_prompt", "user_prompt"]
        }
    }
]


# ============================================================================
# MCP Protocol Handler
# ============================================================================

class MCPProtocol:
    @staticmethod
    def read_request() -> Optional[Dict[str, Any]]:
        try:
            line = sys.stdin.readline()
            if not line:
                return None
            return json.loads(line.strip())
        except (json.JSONDecodeError, EOFError):
            return None
    
    @staticmethod
    def write_response(response: Dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def handle_request(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Route MCP request to appropriate handler."""
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "external-reviewer", "version": "1.0.0"}
            }
        }
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": TOOLS}
        }
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name != "call_ext_reviewer":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
            }
        
        try:
            result = call_ext_reviewer(
                provider=arguments.get("provider"),
                model=arguments.get("model"),
                api_key=arguments.get("api_key"),
                api_key_env=arguments.get("api_key_env"),
                base_url=arguments.get("base_url"),
                temperature=arguments.get("temperature", 0.3),
                max_tokens=arguments.get("max_tokens", 4096),
                system_prompt=arguments.get("system_prompt", ""),
                user_prompt=arguments.get("user_prompt", ""),
            )
            
            result_data = json.loads(result)
            
            if "error" in result_data:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": result_data.get("error")}
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": result}],
                    "isError": result_data.get("status") == "failed"
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": str(e)}
            }
    elif method == "notifications/initialized":
        return None
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }


# ============================================================================
# MCP Server Main Loop
# ============================================================================

def run_server():
    """Run the MCP server main loop."""
    protocol = MCPProtocol()
    while True:
        request = protocol.read_request()
        if request is None:
            break
        response = handle_request(request)
        if response is not None:
            protocol.write_response(response)


if __name__ == "__main__":
    run_server()
