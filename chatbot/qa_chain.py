"""QA chain: retrieve → assemble prompt → LLM → return answer + citations."""
from chatbot.llm_client import complete
from chatbot.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from retrieval.hybrid_search import search


def ask(question: str, top_k: int = 8) -> dict:
    """
    Returns:
        {
            "answer": str,
            "citations": [{"source_file": str, "source_type": str, "text_preview": str}]
        }
    """
    chunks = search(question, top_k=top_k)

    if not chunks:
        return {
            "answer": "I don't have enough information in the knowledge base to answer this.",
            "citations": [],
        }

    user_prompt = build_user_prompt(question, chunks)
    answer = complete(system=SYSTEM_PROMPT, user=user_prompt)

    citations = []
    seen = set()
    for chunk in chunks:
        src = chunk.get("source_file", "unknown")
        if src in seen:
            continue
        seen.add(src)
        citations.append({
            "source_file": src,
            "source_type": chunk.get("source_type", ""),
            "text_preview": chunk.get("text", "")[:200],
        })

    return {"answer": answer, "citations": citations}
