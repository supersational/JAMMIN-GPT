from openai import OpenAI


# https://platform.openai.com/docs/models
# https://openai.com/pricing
# codex models are discontinued

COST_PER_TOKEN = {
    "gpt-4": {"prompt_tokens": 0.03 / 1000, "completion_tokens": 0.06 / 1000},
    "gpt-4-0613": {"prompt_tokens": 0.03 / 1000, "completion_tokens": 0.06 / 1000},
    "gpt-4-32k": {"prompt_tokens": 0.06 / 1000, "completion_tokens": 0.12 / 1000},
    "gpt-4-32k-0613": {"prompt_tokens": 0.06 / 1000, "completion_tokens": 0.12 / 1000},
    "gpt-3.5-turbo": {
        "prompt_tokens": 0.0015 / 1000,
        "completion_tokens": 0.002 / 1000,
    },
    "gpt-3.5-turbo-0613": {
        "prompt_tokens": 0.0015 / 1000,
        "completion_tokens": 0.002 / 1000,
    },
    "gpt-3.5-turbo-16k": {
        "prompt_tokens": 0.003 / 1000,
        "completion_tokens": 0.004 / 1000,
    },
    "gpt-3.5-turbo-16k-0613": {
        "prompt_tokens": 0.003 / 1000,
        "completion_tokens": 0.004 / 1000,
    },
    "gpt-4-1106-preview": {
        "prompt_tokens": 0.01 / 1000,
        "completion_tokens": 0.03 / 1000,
    },
    "gpt-4-1106-vision-preview": {
        "prompt_tokens": 0.01 / 1000,
        "completion_tokens": 0.03 / 1000,
    },
    "gpt-3.5-turbo-1106": { # 16k
        "prompt_tokens": 0.0010 / 1000,
        "completion_tokens": 0.0020 / 1000,
    },
    "gpt-3.5-turbo-instruct": { # 4k context window
        "prompt_tokens": 0.0015 / 1000,
        "completion_tokens": 0.0020 / 1000,
    },
    # "text-davinci-003": {"total_tokens": 0.02 / 1000},
    # "text-davinci-002": {"total_tokens": 0.02 / 1000},
    # "code-davinci-002": {"total_tokens": 0.03 / 1000},
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
    model_num=3,
    system=None,
    frequency_penalty=0.0,
    presence_penalty=0.0,
):
    if model_num == 3:
        model = "gpt-3.5-turbo"
    elif model_num == 4:
        # model = "gpt-4"
        model = "gpt-4-1106-preview"
    else:
        raise Exception("Invalid model_num")
    print("using model", model)
    if system is None:
        messages = [x for x in MESSAGES]
    else:
        messages = [{"role": "system", "content": system}, 
                    {"role": "user", "content": prompt}]

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
