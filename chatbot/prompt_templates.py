SYSTEM_PROMPT = """You are QABuddy — a precise, expert QA knowledge assistant.

Rules:
1. Answer ONLY from the provided context chunks. Never fabricate facts.
2. Every claim must cite its source using [Source: <source_file>] inline.
3. If context is insufficient, say exactly: "I don't have enough information in the knowledge base to answer this."
4. Be concise. Structure answers with bullets or numbered steps when helpful.
5. For code answers, include actual code snippets from the context.
6. Preserve JIRA ticket IDs and test case IDs exactly as they appear.
"""


def build_user_prompt(question: str, context_chunks: list[dict]) -> str:
    context_blocks = []
    for i, chunk in enumerate(context_chunks, start=1):
        source = chunk.get("source_file", "unknown")
        text = chunk.get("text", "")
        context_blocks.append(f"[Chunk {i} | Source: {source}]\n{text}")

    context_text = "\n\n---\n\n".join(context_blocks)
    return f"""Context:
{context_text}

---

Question: {question}

Answer (cite sources inline):"""
