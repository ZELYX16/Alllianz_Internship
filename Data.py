import requests,json


ENCODING_MAP = {
    # GPT-5 Family
    "gpt-5": "o200k_base",
    "gpt-5-mini": "o200k_base",
    "gpt-5-nano": "o200k_base",

    # GPT-4o Family
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",

    # GPT-4.1 Family 
    "gpt-4.1": "o200k_base",
    "gpt-4.1-mini": "o200k_base",
    "gpt-4.1-nano": "o200k_base",

    # GPT-4 Turbo
    "gpt-4-turbo": "cl100k_base",

    # GPT-3.5
    "gpt-3.5-turbo": "cl100k_base",

    # Reasoning Models
    "o1": "o200k_base",
    "o3": "o200k_base",
    "o4-mini": "o200k_base"
}

PRICE_MAP = {
            "gpt-5": {
                "input": 0.00000125,
                "output": 0.00001
            },
            "gpt-5-mini": {
                "input": 0.00000025,
                "output": 0.000002
            },
            "gpt-5-nano": {
                "input": 0.00000005,
                "output": 0.0000004
            },

            "gpt-4o": {
                "input": 0.0000025,
                "output": 0.00001
            },
            "gpt-4o-mini": {
                "input": 0.00000015,
                "output": 0.0000006
            },

            "gpt-4.1": {
                "input": 0.000002,
                "output": 0.000008
            },
            "gpt-4.1-mini": {
                "input": 0.0000004,
                "output": 0.0000016
            },
            "gpt-4.1-nano": {
                "input": 0.0000001,
                "output": 0.0000004
            },

            "gpt-4-turbo": {
                "input": 0.00001,
                "output": 0.00003
            },

            "gpt-3.5-turbo": {
                "input": 0.0000005,
                "output": 0.0000015
            },

            "o1": {
                "input": 0.000015,
                "output": 0.00006
            },
            "o3": {
                "input": 0.000002,
                "output": 0.000008
            },
            "o4-mini": {
                "input": 0.0000011,
                "output": 0.0000044
            }
        }


def fetch_realtime_pricing(supported_models):

    url = "https://openrouter.ai/api/v1/models"

    try:

        response = requests.get(
            url,
            timeout=5
        )

        data = response.json()

    except Exception as err:

        print(
            f"Warning: Live pricing fetch failed ({err}). "
            "Using offline data."
        )

        return {}

    live_prices = {}

    for model in data.get("data", []):

        raw_id = model.get("id", "")

        clean_id = (
            raw_id.split("/")[-1]
            .lower()
        )

        if clean_id in supported_models:

            pricing = model.get(
                "pricing",
                {}
            )

            try:

                live_prices[clean_id] = {

                    "input": float(
                        pricing.get(
                            "prompt",
                            0.0
                        )
                    ),

                    "output": float(
                        pricing.get(
                            "completion",
                            0.0
                        )
                    )
                }

            except (
                ValueError,
                TypeError
            ):

                continue

    return live_prices