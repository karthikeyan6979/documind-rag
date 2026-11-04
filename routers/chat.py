import re
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from config import DISTANCE_THRESHOLD
from state import collection, chat_history
from models import Question, ResetRequest
from services.ollama import get_embedding_single, rewrite_query, stream_ollama_response
from services.prompts import build_prompt

router = APIRouter()


def generate_stream(prompt, history, question, session_id, citations, temperature, top_k):
    full_answer = ""

    for token in stream_ollama_response(prompt, temperature, top_k):
        full_answer += token
        yield token

    history.append((question, full_answer))
    chat_history[session_id] = history

    matches = re.findall(r"\[(\d+)\]", full_answer)
    used_indices = set()
    for match in matches:
        used_indices.add(int(match))

    final_citations = []
    for i, citation in enumerate(citations):
        if i in used_indices:
            final_citations.append(citation)

    print("used_indices:", used_indices)
    print("final_citations:", final_citations)

    yield "\n\n__CITATIONS_START__\n"
    yield json.dumps(final_citations)


@router.post("/chat")
def chat(q: Question):
    session_id = q.session_id or "default"
    history = chat_history.get(session_id, [])
    rewritten_question = rewrite_query(q.question, history)
    question_vector = get_embedding_single(rewritten_question)

    results = collection.query(query_embeddings=[question_vector], n_results=q.n_results)

    scored = []
    
    for document, distance, metadata in zip(results["documents"][0], results["distances"][0], results["metadatas"][0]):
        if distance < DISTANCE_THRESHOLD:
            scored.append((document, distance, metadata))

    scored.sort(key=lambda x: x[1])

    for document, distance, metadata in scored:
            print(f"Page {metadata.get('page')}: {document[:100]}")

    filtered_documents = []
    for document, distance, metadata in scored:
        filtered_documents.append(document)

    if not filtered_documents:
        return {"answer": "No relevant information found in the uploaded document."}

    citations = []
    for document, distance, metadata in scored:
        citation = ({
            "source": metadata["filename"],
            "chunk_index": metadata["chunk_index"],
            "distance": round(distance, 4),
            "context": document[:250] + ("..." if len(document) > 250 else "")
        })
        if "page" in metadata:
            citation["page"] = metadata["page"]
        if "heading" in metadata:
            citation["heading"] = metadata["heading"]

        citations.append(citation)
    for i, c in enumerate(citations):
        print(f"citations[{i}] -> page {c.get('page')}, chunk_index {c.get('chunk_index')}")
    prompt = build_prompt(q.question, filtered_documents, history)

    return StreamingResponse(
        generate_stream(prompt, history, q.question, session_id, citations, q.temperature, q.top_k),
        media_type="text/plain"
    )


@router.post("/chat/reset")
def reset_chat(req: ResetRequest):
    chat_history.pop(req.session_id, None)
    return {"status": "reset", "Session_ID": req.session_id}
