def build_prompt(question, documents, history):
    context_block = "\n\n".join(
        f"[{i}] {doc}" for i, doc in enumerate(documents)
    )
    return f"""Answer the question using ONLY the context below.

RULES:
- Give a complete, well-explained answer using all relevant details from the context — do not just give a one-line answer if the context has more supporting information available.
- State the answer once. Do not repeat it in a different phrasing afterward, and do not write "Therefore, the answer is" or similar summary phrases.
- Do not wrap your answer in quotation marks.
- Write in third person / neutral tone, not first person.
- Every sentence that uses information from the context MUST end with a citation like [0] or [1].
- Use the number that matches the source block below.
- Example: "Python was created by Guido van Rossum [0]. It supports multiple paradigms, including procedural, object-oriented, and functional styles [1]."
- If the context doesn't contain the answer, say so once — do not make up information.

Context:
{context_block}

Question: {question}

History: {history}

Answer (remember to cite every fact with [n]):"""
