import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    timeout=30,
)

# Models to compare (verified live via OpenRouter /api/v1/models)
MODELS = [
    "openai/gpt-5.5",
    "anthropic/claude-opus-4.8",
    "google/gemini-3.1-flash-lite",
    "deepseek/deepseek-v4-flash",
]

# Cost per million tokens (input, output) in USD
PRICES = {
    "openai/gpt-5.5":            (5.00,  30.00),
    "anthropic/claude-opus-4.8": (5.00,  25.00),
    "google/gemini-3.1-flash-lite": (0.25,  1.50),
    "deepseek/deepseek-v4-flash": (0.09,   0.18),
}


def ask(question, model):
    try:
        print(f"\nTesting model: {model}")

        start = time.perf_counter()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=1000
        )

        latency = time.perf_counter() - start

        msg = response.choices[0].message
        # Some reasoning models return None for content and use reasoning_content instead
        answer = msg.content or getattr(msg, "reasoning_content", None) or "(no content returned)"

        prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
        completion_tokens = getattr(response.usage, "completion_tokens", 0)

        input_price, output_price = PRICES.get(model, (0.0, 0.0))

        cost = (
            prompt_tokens * input_price +
            completion_tokens * output_price
        ) / 1_000_000

        return {
            "model": model,
            "answer": answer,
            "latency": latency,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": cost
        }

    except Exception as e:
        return {
            "model": model,
            "error": str(e)
        }


if __name__ == "__main__":
    QUESTION = input("Enter your question: ")

    print(f"\nQuerying {len(MODELS)} models in parallel…")

    results = [None] * len(MODELS)
    with ThreadPoolExecutor(max_workers=len(MODELS)) as executor:
        futures = {executor.submit(ask, QUESTION, model): i for i, model in enumerate(MODELS)}
        for future in as_completed(futures):
            results[futures[future]] = future.result()

    PREVIEW_LEN = 72  # max answer chars shown in the table

    # Build rows: one tuple per model
    rows = []
    for result in results:
        model = result["model"]
        if "error" in result:
            preview = ("ERROR: " + result["error"])[:PREVIEW_LEN]
            latency = "—"
            cost    = "—"
        else:
            text    = result["answer"].replace("\n", " ").strip()
            preview = text[:PREVIEW_LEN - 1] + "…" if len(text) > PREVIEW_LEN else text
            latency = f"{result['latency']:.2f}s"
            cost    = f"${result['cost']:.6f}"
        rows.append((model, preview, latency, cost))

    # Dynamic column widths
    w_model   = max(len(r[0]) for r in rows)
    w_preview = max(len(r[1]) for r in rows)
    w_latency = max(len(r[2]) for r in rows)
    w_cost    = max(len(r[3]) for r in rows)

    header  = (
        f"{'MODEL':<{w_model}}  "
        f"{'ANSWER PREVIEW':<{w_preview}}  "
        f"{'LATENCY':>{w_latency}}  "
        f"{'COST':>{w_cost}}"
    )
    divider = "─" * len(header)

    print(f"\nQ: {QUESTION}\n")
    print(header)
    print(divider)
    for model, preview, latency, cost in rows:
        print(
            f"{model:<{w_model}}  "
            f"{preview:<{w_preview}}  "
            f"{latency:>{w_latency}}  "
            f"{cost:>{w_cost}}"
        )
    print()