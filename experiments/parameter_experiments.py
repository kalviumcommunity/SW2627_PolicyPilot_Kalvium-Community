import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

MODEL = os.getenv("CHAT_MODEL", "llama-3.1-8b-instant")

client = OpenAI(
    base_url=os.getenv("API_BASE_URL"),
    api_key=os.getenv("API_KEY"),
)

QUESTION = "What is the maximum number of days employees can work remotely?"

CONTEXT = """
Employees may work remotely for a maximum of 3 days per week.
Any additional remote work requires manager approval.
"""

OUTPUT_PATH = Path("outputs/parameter_experiment_results.json")


# ============================================================
# RESULTS
# ============================================================

results = {
    "temperature_experiment": [],
    "max_tokens_experiment": [],
    "stop_experiment": {},
}


# ============================================================
# COMMON MODEL CALL
# ============================================================

def call_model(
    temperature=0.1,
    max_tokens=150,
    stop=None,
):
    """
    Call the LLM with configurable generation parameters.
    """

    params = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are PolicyPilot, a grounded company policy "
                    "assistant.\n\n"
                    "Answer ONLY using the provided policy context.\n"
                    "Do not use outside knowledge.\n"
                    "Do not guess or invent information.\n"
                    "Do not provide reasoning or analysis.\n"
                    "Return only the concise final answer.\n\n"
                    f"Policy context:\n{CONTEXT}"
                ),
            },
            {
                "role": "user",
                "content": QUESTION,
            },
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if stop is not None:
        params["stop"] = stop

    response = client.chat.completions.create(**params)

    return response.choices[0].message.content or ""


# ============================================================
# TASK 1 - TEMPERATURE EXPERIMENT
# ============================================================

print("\n" + "=" * 70)
print("TASK 1 - TEMPERATURE EXPERIMENT")
print("=" * 70)

print("\nSame question and same policy context are used for every test.")
print("Only the temperature is changed.")

for temperature in [0.0, 0.2, 1.0]:

    print(f"\nTEMPERATURE = {temperature}")
    print("-" * 70)

    outputs = []

    for run in range(1, 4):

        output = call_model(
            temperature=temperature,
            max_tokens=150,
        )

        outputs.append(output)

        print(f"\nRun {run}:")
        print(output)

    results["temperature_experiment"].append(
        {
            "temperature": temperature,
            "outputs": outputs,
        }
    )


# ============================================================
# TASK 2 - MAX TOKENS EXPERIMENT
# ============================================================

print("\n" + "=" * 70)
print("TASK 2 - MAX_TOKENS EXPERIMENT")
print("=" * 70)

print("\nThe same question is used with different output limits.")

for max_tokens in [30, 150]:

    output = call_model(
        temperature=0.1,
        max_tokens=max_tokens,
    )

    print(f"\nMAX_TOKENS = {max_tokens}")
    print("-" * 70)
    print(output)

    print(f"\nOutput length: {len(output)} characters")

    results["max_tokens_experiment"].append(
        {
            "max_tokens": max_tokens,
            "output": output,
            "output_length_characters": len(output),
        }
    )


# ============================================================
# TASK 3 - STOP EXPERIMENT
# ============================================================

print("\n" + "=" * 70)
print("TASK 3 - STOP EXPERIMENT")
print("=" * 70)

print(
    "\nTesting whether the stop sequence prevents generation "
    "from continuing after the answer."
)


def call_stop_model(stop=None):

    params = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are PolicyPilot.\n"
                    "Use only the provided policy.\n"
                    "Do not use outside knowledge.\n"
                    "Do not provide reasoning.\n"
                    "Return the answer followed by an explanation.\n\n"
                    f"Policy:\n{CONTEXT}"
                ),
            },
            {
                "role": "user",
                "content": (
                    "Answer this question in the following format:\n\n"
                    "Answer: <answer>\n"
                    "Explanation: <explanation>\n\n"
                    f"Question: {QUESTION}"
                ),
            },
        ],
        "temperature": 0.0,
        "max_tokens": 150,
    }

    if stop is not None:
        params["stop"] = stop

    response = client.chat.completions.create(**params)

    return response.choices[0].message.content or ""


# Without stop
without_stop = call_stop_model()

# With stop
with_stop = call_stop_model(
    stop=["Explanation:"]
)


print("\nWITHOUT STOP")
print("-" * 70)
print(without_stop)

print("\nWITH STOP = ['Explanation:']")
print("-" * 70)
print(with_stop)


results["stop_experiment"] = {
    "without_stop": without_stop,
    "with_stop": {
        "stop": ["Explanation:"],
        "output": with_stop,
    },
}


# ============================================================
# SAVE RESULTS
# ============================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

with OUTPUT_PATH.open(
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        results,
        file,
        indent=2,
        ensure_ascii=False,
    )


# ============================================================
# EXPERIMENT SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("EXPERIMENT SUMMARY")
print("=" * 70)

print(
    """
Task 1 - Temperature
--------------------
0.0 -> Lowest randomness and highest consistency
0.2 -> Low randomness with slight variation
1.0 -> Higher variation in wording/output

Task 2 - max_tokens
-------------------
30  -> Short output and may be truncated
150 -> Allows a longer response

Task 3 - stop
-------------
Without stop -> Model can continue into the explanation
With stop    -> Generation stops when 'Explanation:' is reached

Recommended grounded-task settings
-----------------------------------
temperature = 0.0 to 0.1
max_tokens  = 150
top_p       = 1.0
stop        = Optional
"""
)

print("=" * 70)
print("EXPERIMENT COMPLETE")
print("=" * 70)

print(f"Results saved to: {OUTPUT_PATH}")