from openai import OpenAI


# https://platform.openai.com/docs/models
# https://openai.com/pricing
COST_PER_TOKEN = {
    # --- GPT-5 Family (Flagship) ---
    "gpt-5.2": {
        "prompt_tokens": 1.75 / 1_000_000,
        "completion_tokens": 14.00 / 1_000_000,
    },
    "gpt-5.1": {
        "prompt_tokens": 1.25 / 1_000_000,
        "completion_tokens": 10.00 / 1_000_000,
    },
    "gpt-5": {
        "prompt_tokens": 1.25 / 1_000_000,
        "completion_tokens": 10.00 / 1_000_000,
    },
    "gpt-5-mini": {
        "prompt_tokens": 0.25 / 1_000_000,
        "completion_tokens": 2.00 / 1_000_000,
    },
    "gpt-5-nano": {
        "prompt_tokens": 0.05 / 1_000_000,
        "completion_tokens": 0.40 / 1_000_000,
    },
    # --- GPT-4.1 Family ---
    "gpt-4.1": {
        "prompt_tokens": 2.00 / 1_000_000,
        "completion_tokens": 8.00 / 1_000_000,
    },
    "gpt-4.1-mini": {
        "prompt_tokens": 0.40 / 1_000_000,
        "completion_tokens": 1.60 / 1_000_000,
    },
    "gpt-4.1-nano": {
        "prompt_tokens": 0.10 / 1_000_000,
        "completion_tokens": 0.40 / 1_000_000,
    },
    # --- GPT-4o Family  ---
    "gpt-4o": {
        "prompt_tokens": 2.50 / 1_000_000,
        "completion_tokens": 10.00 / 1_000_000,
    },
    "gpt-4o-2024-05-13": {
        "prompt_tokens": 5.00 / 1_000_000,
        "completion_tokens": 15.00 / 1_000_000,
    },
    "gpt-4o-mini": {
        "prompt_tokens": 0.15 / 1_000_000,
        "completion_tokens": 0.60 / 1_000_000,
    },
}


def calculate_cost(usage, model):
    cost = 0.0
    for key, value in usage.items():
        if key in COST_PER_TOKEN[model]:
            cost += value * COST_PER_TOKEN[model][key]
    return cost


SYSTEM = """You are a helpful AI assistant. Respond to the user's requests exactly as they are given."""  # noqa: E501
# SYSTEM = f"""
# You are a helpful AI assistant. Respond to the user's requests exactly as they are given.
# You generate music in ABC notation, responding only with notation and no other text.
# It is important that ONLY parseable ABC notation is in your replies.
# You must include X:, K: and all necessary fields in your output""".strip()

MESSAGES = [
    {"role": "system", "content": SYSTEM},
    # {"role": "user", "content": PROMPT},
]


def get_completion(
    prompt: str,
    model_name: str = "gpt-5-mini",
    system: str | None = None,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
):
    """Obtain a chat completion.

    model_name: explicit OpenAI model string (e.g. "gpt-5-mini", "gpt-4o").
    If the model name contains the substring "gpt-5" we omit adjustable
    temperature / penalties because those endpoints currently fix temperature.
    """
    model = model_name
    print("using model", model)
    if system is None:
        messages = [x for x in MESSAGES]
    else:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

    client = OpenAI()
    if "gpt-5" in model_name:
        # gpt-5 family: simplified params (temp fixed server-side)
        completion = client.chat.completions.create(
            model=model,
            messages=messages
        )
    else:

        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
    # usage = completion["usage"]
    # cost = calculate_cost(usage, model)
    # print("API cost:" cost)

    return completion
