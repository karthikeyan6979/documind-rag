import json
import requests
from config import OLLAMA_URL, GENERATION_MODEL, EMBEDDING_MODEL


def get_embeddings_batch(texts: list[str]):
    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": texts}
    )
    data = response.json()
    embeddings = data.get("embeddings")

    if not embeddings or len(embeddings) != len(texts):
        raise ValueError(f"Mismatch or empty response: expected {len(texts)}, got {len(embeddings) if embeddings else 0}")

    for i, e in enumerate(embeddings):
        if not e:
            raise ValueError(f"Empty embedding at index {i} for text: {texts[i][:80]!r}")

    return embeddings


def get_embedding_single(text: str):

    return get_embeddings_batch([text])[0]


def rewrite_query(question, history):
    if not history:
        return question
    history_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in history])
    prompt = f""" Given the conversation history and a new question, decide if the new question depends on the history (e.g. uses pronouns like "it", "that", "this", or is otherwise incomplete without context).

    If it depends on history, rewrite it to be a standalone question.
    If it does NOT depend on history (it's already a complete, standalone question), return it EXACTLY as-is, unchanged.

    New Question:
    {question}
    History:
    {history_text}
    """
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json = {
            "model": GENERATION_MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.2}
        }
    )

    return response.json()["response"].strip()


def stream_ollama_response(prompt, temperature = 0.3, top_k = 40):
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": GENERATION_MODEL,
            "prompt": prompt,
            "stream": True,
            "think": False,
            "options" : {
                "temperature": temperature,
                "top_k": top_k
            }
        },
        stream=True
    )

    for line in response.iter_lines():
        if line:
            data = json.loads(line)

            token = data.get("response", "")

            if token:
                yield token
