import os
from typing import Optional

from django.conf import settings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from documents.embeddings import search_similar_chunks

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free"),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=0.2,
            timeout=180,
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "LLM Document QA",
            },
        )
    return _llm


RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a question-answering assistant that responds to questions based only on the provided document text.

Important rules:
1. Use only the information available in the document text.
2. If the answer is not found in the documents, explicitly state: "The answer was not found in the provided documents."
3. Do not add any information from your own knowledge.
4. Respond in fluent, natural Persian.
"""),
    ("human", """Document text:
{context}

User question:
{question}

Answer:"""),
])


def build_context(chunks: list) -> str:
    if not chunks:
        return "(هیچ سند مرتبطی یافت نشد)"

    parts = []
    for i, c in enumerate(chunks, 1):
        title = c.get("document_title", "بدون عنوان")
        idx = c.get("chunk_index", "?")
        content = c.get("content", "").strip()
        parts.append(f"[منبع {i} | سند: {title} | تکه {idx}]\n{content}")

    return "\n\n---\n\n".join(parts)


def answer_question(question: str, k: int = 4, document_id: Optional[int] = None) -> dict:
    if not question or not question.strip():
        raise ValueError("متن سوال نمی‌تواند خالی باشد.")
        
    chunks = search_similar_chunks(question, k=k, document_id=document_id)

    context = build_context(chunks)

    llm = get_llm()
    chain = RAG_PROMPT | llm | StrOutputParser()

    answer = chain.invoke({
        "context": context,
        "question": question,
    })

    return {
        "question": question,
        "answer": answer.strip(),
        "sources": chunks,
    }