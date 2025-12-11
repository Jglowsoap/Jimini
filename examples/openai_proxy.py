"""
Example: Jimini as OpenAI Proxy

This example shows how to use Jimini as a transparent proxy for OpenAI API requests.
All requests are evaluated against policies before being forwarded to OpenAI.

Deploy this proxy and point your applications to it instead of api.openai.com.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import os
import json


app = FastAPI(
    title="Jimini OpenAI Proxy",
    description="Policy-enforcing proxy for OpenAI API with Jimini guardrails"
)

JIMINI_URL = os.getenv("JIMINI_URL", "http://localhost:9000")
JIMINI_API_KEY = os.getenv("JIMINI_API_KEY", "changeme")
OPENAI_URL = "https://api.openai.com/v1"


async def evaluate_with_jimini(text: str, direction: str) -> dict:
    """Evaluate text with Jimini policy engine"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{JIMINI_URL}/v1/evaluate",
            json={
                "text": text,
                "direction": direction,
                "api_key": JIMINI_API_KEY
            },
            timeout=5.0
        )
        resp.raise_for_status()
        return resp.json()


@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: Request):
    """
    Proxy OpenAI chat completions with policy enforcement.
    
    Checks:
    - User messages for PII, prompt injection, toxicity
    - Assistant responses for sensitive data leakage
    """
    body = await request.json()
    
    # Extract the last user message
    messages = body.get("messages", [])
    last_user_message = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break
    
    if last_user_message:
        # Check user input with Jimini
        eval_result = await evaluate_with_jimini(last_user_message, "user_to_llm")
        
        if eval_result["decision"] == "block":
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "message": f"Policy violation: {eval_result.get('message', 'Request blocked')}",
                        "type": "policy_violation",
                        "code": "jimini_blocked",
                        "rules": eval_result.get("rule_ids", [])
                    }
                }
            )
        
        if eval_result["decision"] == "flag":
            # Log flag but allow request
            print(f"⚠️ Flagged request: {eval_result.get('rule_ids', [])}")
    
    # Forward to OpenAI
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    try:
        async with httpx.AsyncClient() as client:
            openai_resp = await client.post(
                f"{OPENAI_URL}/chat/completions",
                json=body,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                },
                timeout=60.0
            )
            openai_resp.raise_for_status()
            response_data = openai_resp.json()
        
        # Check assistant response
        if "choices" in response_data:
            for choice in response_data["choices"]:
                if "message" in choice and "content" in choice["message"]:
                    assistant_message = choice["message"]["content"]
                    
                    eval_result = await evaluate_with_jimini(assistant_message, "llm_to_user")
                    
                    if eval_result["decision"] == "block":
                        return JSONResponse(
                            status_code=403,
                            content={
                                "error": {
                                    "message": "Assistant response blocked by policy",
                                    "type": "policy_violation",
                                    "code": "jimini_blocked_output",
                                    "rules": eval_result.get("rule_ids", [])
                                }
                            }
                        )
                    
                    if eval_result["decision"] == "flag":
                        print(f"⚠️ Flagged response: {eval_result.get('rule_ids', [])}")
        
        return JSONResponse(content=response_data)
    
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=e.response.json()
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e), "type": "proxy_error"}}
        )


@app.post("/v1/completions")
async def proxy_completions(request: Request):
    """Proxy for legacy completions endpoint"""
    body = await request.json()
    prompt = body.get("prompt", "")
    
    if prompt:
        eval_result = await evaluate_with_jimini(prompt, "user_to_llm")
        
        if eval_result["decision"] == "block":
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "message": "Policy violation",
                        "type": "policy_violation",
                        "rules": eval_result.get("rule_ids", [])
                    }
                }
            )
    
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    async with httpx.AsyncClient() as client:
        openai_resp = await client.post(
            f"{OPENAI_URL}/completions",
            json=body,
            headers={
                "Authorization": auth_header,
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
        return JSONResponse(content=openai_resp.json())


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "jimini-openai-proxy"}


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Jimini OpenAI Proxy on http://localhost:8080")
    print(f"📡 Jimini Gateway: {JIMINI_URL}")
    print("\nUsage:")
    print("  export OPENAI_API_BASE=http://localhost:8080/v1")
    print("  # Your OpenAI SDK calls will now go through Jimini")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
