import os
import json
import time
import csv
import ollama


# ==========================================
# COMMERCIAL CLOUD HOSTING RATES
# ==========================================
PRICE_INPUT_STD = 0.25
PRICE_OUTPUT = 0.25

ALLOWED_CATEGORIES = ["Bug", "Feature Request", "Billing", "Other"]

MODEL_ID = "mistral"


# ==========================================
# PROMPTS
# ==========================================

# v1: Zero-Shot 
PROMPT_V1 = (
    f"Classify the ticket into exactly one category: {ALLOWED_CATEGORIES}.\n"
    f"Respond with exactly one category name from the list above, and nothing else. "
    f"No punctuation. No explanation. No restating the ticket."
)

# v2: Few-Shot 
PROMPT_V2_FEW_SHOT = (
    f"Classify the customer ticket into exactly one category: {ALLOWED_CATEGORIES}.\n\n"
    "EXAMPLES:\n"
    "Ticket: 'App crashes with error 500 during card processing.'\n"
    "Category: Bug\n\n"
    "Ticket: 'Double charged for this month subscription billing.'\n"
    "Category: Billing\n\n"
    "Ticket: 'Requesting a dark mode toggle inside user settings.'\n"
    "Category: Feature Request\n\n"
    "Ticket: 'What are your operational hours over the holidays?'\n"
    "Category: Other\n\n"
    "Now classify the following ticket.\n"
    "Respond with exactly one category name from the list above, and nothing else. "
    "No punctuation. No explanation. No restating the ticket."
)

# v3: Chain-of-Thought 
PROMPT_V3_COT = (
    f"You are an expert customer support routing AI. "
    f"Classify the customer ticket into exactly one of: {ALLOWED_CATEGORIES}.\n\n"

    f"EXAMPLES:\n"
    f"Input: 'App crashes with error 500 during card processing.' -> Output: Bug\n"
    f"Input: 'Double charged for this month subscription billing.' -> Output: Billing\n"
    f"Input: 'Requesting a dark mode toggle inside user settings.' -> Output: Feature Request\n"
    f"Input: 'What are your operational hours over the holidays?' -> Output: Other\n\n"

    "For each ticket, reason using these steps:\n"
    "1. Identify the primary issue mentioned in the ticket.\n"
    "2. Extract important keywords or phrases.\n"
    "3. Determine the user's intent (reporting a problem, requesting a new capability, "
    "asking about billing/payment, or making a general inquiry).\n"
    "4. Compare the intent against the available categories:\n"
    "   - Bug: Existing functionality is broken, failing, or behaving unexpectedly.\n"
    "   - Feature Request: User wants a new feature, enhancement, or improvement.\n"
    "   - Billing: Payment, refund, invoice, subscription, or charge-related issue.\n"
    "   - Other: Anything that does not fit the above categories.\n"
    "5. Select the single best category.\n\n"

    'Respond as JSON: {"reasoning": "...", "category": "..."}'
)


def calculate_run_cost(total_in, total_out):
    """Calculates simulated production costs."""
    cost_in = (total_in / 1_000_000) * PRICE_INPUT_STD
    cost_out = (total_out / 1_000_000) * PRICE_OUTPUT
    return cost_in + cost_out


def call_ollama(system_prompt, user_ticket, is_json=False):
    kwargs = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_ticket}
        ],
        "options": {
            "temperature": 0.0
        }
    }

    if is_json:
        kwargs["format"] = "json"

    try:
        response = ollama.chat(**kwargs)
        return response
    except Exception as e:
        print(f"\n[ CONNECTION ERROR]  Error: {str(e)}")
        return None


def extract_category_plain_text(raw_text):
    """
    Defensive parser for plain-text (non-JSON) responses.
    Takes the first line only, then matches it against the allowed
    categories (case-insensitive substring match). Falls back to
    'Parsing Error' if nothing matches.
    """
    first_line = raw_text.strip().split("\n")[0]
    cleaned = first_line.replace(".", "").replace("\"", "").strip()

    for cat in ALLOWED_CATEGORIES:
        if cat.lower() in cleaned.lower():
            return cat

    return "Parsing Error"


def extract_category_json(raw_text):
    """
    Defensive parser for JSON responses. Parses the JSON object and
    validates the 'category' field against the allowed categories.
    """
    try:
        parsed = json.loads(raw_text)
        candidate = str(parsed.get("category", "")).strip()
    except Exception:
        return "JSON Parse Failure"

    for cat in ALLOWED_CATEGORIES:
        if cat.lower() == candidate.lower():
            return cat

    # fallback: substring match in case of minor formatting drift e.g. "Bug."
    for cat in ALLOWED_CATEGORIES:
        if cat.lower() in candidate.lower():
            return cat

    return "Parsing Error"


def run_evaluation_cycle(version_name, prompt_payload, dataset, is_json=False):
    print(f"Executing Local Benchmark Run: {version_name:<25} ... ", end="", flush=True)

    start_time = time.time()
    total_in = 0
    total_out = 0
    correct = 0
    evaluated = 0

    for ticket in dataset:

        response_data = call_ollama(prompt_payload, ticket["text"], is_json)

        if not response_data:
            print(f"\n   [ Skipped Ticket #{ticket['id']}: Ollama connection failed]")
            continue

        # Extract Ollama's native token counts
        total_in += response_data.get("prompt_eval_count", 0)
        total_out += response_data.get("eval_count", 0)

        raw_text = response_data.get("message", {}).get("content", "").strip()

        print(raw_text)
        if is_json:
            predicted = extract_category_json(raw_text)
        else:
            predicted = extract_category_plain_text(raw_text)

        evaluated += 1

        if predicted.lower() == ticket["expected"].lower():
            correct += 1

    duration = time.time() - start_time
    accuracy = (correct / evaluated) * 100 if evaluated else 0
    cost_usd = calculate_run_cost(total_in, total_out)

    print(f"DONE ({duration:.2f}s) [Acc: {accuracy:>5.1f}% | Proj. Cost: ${cost_usd:.6f}]")

    return {
        "Version": version_name,
        "Accuracy (%)": round(accuracy, 2),
        "Total Input Tokens": total_in,
        "Total Output Tokens": total_out,
        "Projected Cost (USD)": round(cost_usd, 6)
    }


def save_to_csv(reports, filename="benchmark_results.csv"):
    """Exports the benchmarking dashboard metrics to a CSV file."""
    if not reports:
        return

    keys = reports[0].keys()

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(reports)

    print(f"\n Successfully exported local metrics to '{filename}'!")


if __name__ == "__main__":
    if not os.path.exists("tickets.json"):
        raise FileNotFoundError("CRITICAL: 'tickets.json' not found in current directory.")

    with open("tickets.json", "r") as f:
        dataset = json.load(f)

    print(f"\n{'='*80}\n STARTING LOCAL OLLAMA BENCHMARK PIPELINE (Model: {MODEL_ID})\n{'='*80}")

    reports = [
        run_evaluation_cycle("v1_Zero-Shot ", PROMPT_V1, dataset, is_json=False),
        run_evaluation_cycle("v2_Few-Shot ", PROMPT_V2_FEW_SHOT, dataset, is_json=False),
        run_evaluation_cycle("v3_CoT ", PROMPT_V3_COT, dataset, is_json=True)
    ]

    print(f"\n\n{'='*80}\nFINAL PRODUCTION BENCHMARK DASHBOARD \n{'='*80}")
    print(f"{'Version':<25} | {'Accuracy':<9} | {'Input Tokens':<13} | {'Output Tokens':<13} | {'Proj. Cost ($)':<12}")
    print("-" * 80)
    for r in reports:
        print(f"{r['Version']:<25} | {r['Accuracy (%)']:>7.1f}% | {r['Total Input Tokens']:>13} | {r['Total Output Tokens']:>13} | ${r['Projected Cost (USD)']:>11.6f}")
    print(f"{'='*80}")

    save_to_csv(reports)