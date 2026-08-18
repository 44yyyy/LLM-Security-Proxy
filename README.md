# Building an LLM Security Proxy

## Introduction & Motivation
This project explores how enterprise Large Language Model (LLM) firewalls and guards work under the hood. As generative AI adoption grows, companies are relying on commercial LLM security gateways to prevent sensitive data leaks. I wanted to try building a prototype of it myself to understand the mechanics behind it.

My main objective was to build a zero-trust asynchronous proxy that sits between a user and an LLM, actively redacting PII and blocking prompt injections. However, I encountered some challenges along the way that made me dive deep into machine learning concepts and consider the trade-offs required to build reliable security systems.

### Technologies & Tools Used
*   **Languages:** Python 3.10+
*   **Frameworks:** FastAPI, `httpx` (Asynchronous HTTP)
*   **Machine Learning/NLP:** Microsoft Presidio, spaCy NER (Named Entity Recognition)
*   **Environment:** REST APIs, Local LLM Integration (Ollama / LLaMA 3.2)

## 1. Asynchronous Proxy
The very first thing that I needed was a way to intercept the traffic for analysis. I decided to build a reverse proxy using FastAPI. 

I learned that standard LLM APIs like OpenAI or Ollama format conversations as a JSON payload containing a messages array where each entry holds a role (user/assistant) and the raw content (prompt). The proxy needed to intercept this incoming payload, iterate through the array to extract and sanitize the prompt, and finally, reconstruct the safe payload before forwarding it to the LLM."

Payloads were being intercepted before they could reach the untrusted LLM environment.

## 2. Implementing Data Loss Prevention (DLP)
For the main security feature of the project, I decided to integrate Microsoft Presidio and spaCy's Named Entity Recognition (NER) models to analyze the text and implement DLP.

Instead of relying on regex, which could easily be bypassed or be prone to errors, the NER model understands the context of the prompt. I wrote a `clear_pii` function that scans the prompt, identifies PII entities like credit card numbers, email addresses, social security numbers, and replaces them with safe placeholders. 

Here is a demonstration:

**cURL Request:** `curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      { 
        "role": "user", 
        "content": "Hi! Please update my information. My email is john.doe@company.com, and my credit card number is 4111-1111-1111-1111."     
      }
    ]
  }'`

![1](Screenshots/1.jpg)

The POST request is intercepted, with the PII inside the prompt being redacted.

![2](Screenshots/2.jpg)

After the filter was applied to the prompt, the request is completed, with the AI response now being returned to us.
