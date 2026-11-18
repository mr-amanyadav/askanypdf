import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import GROQ_API_KEY, LLM_MODEL
from retrieval.retriever import retrieve_context

_groq = None


def _llm():
    global _groq
    if _groq is None:
        from groq import Groq
        _groq = Groq(api_key=GROQ_API_KEY)
    return _groq


COT_PROMPT = """You are a retrieval-augmented QA system. Answer using ONLY the evidence below.

=== PAGE CONTENT ===
{page_text}

=== CROSS-PAGE SUMMARIES ===
{summary_text}

=== QUESTION ===
{question}

Respond in this EXACT format:

STEP-BY-STEP ANALYSIS:
1. ...
2. ...
3. ...

REASONING SUMMARY: <one sentence>

RELEVANT PAGES: <comma-separated page numbers>

FINAL ANSWER: <the direct answer>"""


def answer_stream(doc_id: str, question: str):
    """Generator: yields streaming chunks of the answer."""
    ctx = retrieve_context(doc_id, question)

    prompt = COT_PROMPT.format(
        page_text=ctx["page_text"],
        summary_text=ctx["summary_text"],
        question=question,
    )

    # Stream from Groq
    stream = _llm().chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000,
        stream=True,
    )

    full_answer = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            full_answer += delta
            yield {"type": "token", "content": delta}

    # Emit citations at the end
    yield {
        "type": "done",
        "answer": full_answer,
        "top_pages": ctx["top_pages"],
        "num_candidates": ctx["num_candidates"],
    }