from openai import OpenAI


# https://platform.openai.com/docs/models
# https://openai.com/pricing
# codex models are discontinued

COST_PER_TOKEN = {
    "gpt-4o": {
        "prompt_tokens": 5.00 / 1_000_000,
        "completion_tokens": 15.00 / 1_000_000,
    },
    "gpt-4o-2024-05-13": {
        "prompt_tokens": 5.00 / 1_000_000,
        "completion_tokens": 15.00 / 1_000_000,
    },
    "gpt-4o-mini": {
        "prompt_tokens": 0.15 / 1_000_000,
        "completion_tokens": 0.60 / 1_000_000,
    },
    "gpt-4o-mini-2024-07-18": {
        "prompt_tokens": 0.15 / 1_000_000,
        "completion_tokens": 0.60 / 1_000_000,
    },
    "gpt-3.5-turbo-0125": {
        "prompt_tokens": 0.50 / 1_000_000,
        "completion_tokens": 1.50 / 1_000_000,
    },
    "gpt-3.5-turbo-instruct": {
        "prompt_tokens": 1.50 / 1_000_000,
        "completion_tokens": 2.00 / 1_000_000,
    },
    "text-embedding-3-small": {"total_tokens": 0.02 / 1_000_000},
    "text-embedding-3-large": {"total_tokens": 0.13 / 1_000_000},
    "ada-v2": {"total_tokens": 0.10 / 1_000_000},
    "gpt-3.5-turbo": {
        "prompt_tokens": 3.00 / 1_000_000,
        "completion_tokens": 6.00 / 1_000_000,
        "training_tokens": 8.00 / 1_000_000,
    },
    "davinci-002": {
        "prompt_tokens": 12.00 / 1_000_000,
        "completion_tokens": 12.00 / 1_000_000,
        "training_tokens": 6.00 / 1_000_000,
    },
    "babbage-002": {
        "prompt_tokens": 1.60 / 1_000_000,
        "completion_tokens": 1.60 / 1_000_000,
        "training_tokens": 0.40 / 1_000_000,
    },
    "gpt-4-turbo": {
        "prompt_tokens": 10.00 / 1_000_000,
        "completion_tokens": 30.00 / 1_000_000,
    },
    "gpt-4-0125-preview": {
        "prompt_tokens": 10.00 / 1_000_000,
        "completion_tokens": 30.00 / 1_000_000,
    },
    "gpt-4-1106-preview": {
        "prompt_tokens": 10.00 / 1_000_000,
        "completion_tokens": 30.00 / 1_000_000,
    },
    "gpt-4-vision-preview": {
        "prompt_tokens": 10.00 / 1_000_000,
        "completion_tokens": 30.00 / 1_000_000,
    },
    "gpt-3.5-turbo-1106": {
        "prompt_tokens": 1.00 / 1_000_000,
        "completion_tokens": 2.00 / 1_000_000,
    },
    "gpt-3.5-turbo-0613": {
        "prompt_tokens": 1.50 / 1_000_000,
        "completion_tokens": 2.00 / 1_000_000,
    },
    "gpt-3.5-turbo-16k-0613": {
        "prompt_tokens": 3.00 / 1_000_000,
        "completion_tokens": 4.00 / 1_000_000,
    },
    "gpt-3.5-turbo-0301": {
        "prompt_tokens": 1.50 / 1_000_000,
        "completion_tokens": 2.00 / 1_000_000,
    },
    # "text-davinci-003": {"total_tokens": 20 / 1_000_000},
    # "text-davinci-002": {"total_tokens": 20 / 1_000_000},
    # "code-davinci-002": {"total_tokens": 30 / 1_000_000},
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
    prompt,
    model_num=4,
    system=None,
    frequency_penalty=0.0,
    presence_penalty=0.0,
):
    if model_num == 3:
        model = "gpt-3.5-turbo"
    elif model_num == 4:
        model = "gpt-4o-mini"
    else:
        raise Exception("Invalid model_num")
    print("using model", model)
    if system is None:
        messages = [x for x in MESSAGES]
    else:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

    client = OpenAI()

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
