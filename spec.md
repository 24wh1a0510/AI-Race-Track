# Spec — Multi-Model Comparison Tool
 
## Goal
Ask one question to four LLMs via OpenRouter and show each answer
with its speed and cost, so I can compare models for a real task.
 
## Input
- A single question (string). Hardcode first; later read from input.
 
## Output (per model)
- answer text   - latency (seconds)   - tokens (in/out)   - cost (USD)
 
## Models (OpenRouter IDs)
"google/gemma-3-27b-it:free",
    "qwen/qwen3-32b:free"
## Pipeline
1. Load OPENROUTER_API_KEY from .env.
2. For each model: send the question, time the call, read token usage.
3. cost = in_tokens*in_price + out_tokens*out_price.
4. Print all four results side by side.
 
## Error handling
- Wrap each model call in try/except; on failure, log it and continue.
 
## Done when
- One run shows four answers, each with speed and cost.
- One failing model does not stop the others.
- No API key appears in the code.
