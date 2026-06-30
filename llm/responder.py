"""Stream a corporate-speak response from a local Ollama model.

Talks to Ollama on http://localhost:11434 (start it with `ollama serve`). Nothing
leaves the machine. Swap MODEL to a beefier local model (e.g. "qwen2.5:7b") if the
jargon feels flat — remember to `ollama pull` it first.
"""

import random

import ollama

from llm.prompt import SYSTEM_PROMPT, build_prompt

MODEL = "llama3.2:3b"


def stream_response(transcript: str, on_token) -> str:
    """Stream a response for ``transcript``.

    ``on_token`` is called with each text chunk as it arrives. Returns the full
    response once streaming completes.
    """
    full = []
    stream = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *build_prompt(transcript),
        ],
        options={
            # Higher temp + top_p => wittier, more varied slop. A fresh random
            # seed each call keeps identical transcripts from repeating verbatim.
            # repeat_penalty stops the small model looping on its own jargon.
            "temperature": 1.0,
            "top_p": 0.95,
            "repeat_penalty": 1.15,
            "num_predict": 160,
            "seed": random.randint(0, 2**31 - 1),
        },
        stream=True,
    )
    for chunk in stream:
        token = chunk["message"]["content"]
        if token:
            full.append(token)
            on_token(token)
    return "".join(full)


if __name__ == "__main__":
    # Quick isolation test (requires `ollama serve` + the model pulled).
    stream_response(
        "We need to align on Q3 roadmap priorities before the next sprint.",
        lambda t: print(t, end="", flush=True),
    )
    print()
