import os
import httpx

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from transformers import pipeline

app = FastAPI(title="LLM-Guard", version="1.0")

apikey = os.getenv("apikey", "ollama_local")
apiurl = os.getenv("apiurl", "http://localhost:11434/v1/chat/completions")

# Initialize Presidio
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def clear_pii(text: str) -> str:
    """Looks for PII in text and replaces it with safe placeholders"""
    # Analyze text for PII entities
    results = analyzer.analyze(
        text=text,
        entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN"],
        language="en"
    )
    # Anonymize
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized_result.text

@app.post("/v1/chat/completions")
async def chat_completions_proxy(request: Request):
    if not apikey:
        raise HTTPException(status_code=500, detail="LLM API key missing.")

    try:
        user_payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    # Intercept and redact user prompt
    # Iterate thru messages array and sanitize 'content'
    if "messages" in user_payload:
        for message in user_payload["messages"]:
            if "content" in message and isinstance(message["content"], str):
                original_text = message["content"]

                safe_text = clear_pii(original_text)

                print(f"\nRaw Prompt:      {original_text}") # Prompt Logging
                print(f"Redacted Prompt: {safe_text}\n") 
                
                message["content"] = safe_text  # Overwrite

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {apikey}"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                apiurl,
                json=user_payload,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as e:
            return JSONResponse(status_code=e.response.status_code, content=e.response.json())
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Failed to communicate with LLM: {str(e)}")

    return response.json()