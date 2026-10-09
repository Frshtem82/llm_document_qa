# check.py
from documents.models import Document, DocumentChunk
from documents.embeddings import get_index_count, search_similar_chunks
from qa.services import build_context

print("=" * 60)
print("DOCUMENTS")
print("=" * 60)
for d in Document.objects.all():
    print(f"ID={d.id} | title={d.title}")
    print(f"  has_text={bool(d.full_text)} | len={len(d.full_text) if d.full_text else 0}")
    print(f"  processed={d.is_processed} | chunks={d.chunks.count()}")

print()
print("=" * 60)
print("QDRANT")
print("=" * 60)
print(f"Points: {get_index_count()}")

print()
print("=" * 60)
print("SEARCH TEST: 'زندان کجاست؟'")
print("=" * 60)
results = search_similar_chunks("زندان کجاست؟", k=5)
print(f"Results: {len(results)}")
for r in results:
    print(f"  score={r['score']:.4f} | {r['document_title']} | chunk {r['chunk_index']}")
    print(f"  content: {r['content'][:150]}")
    print()

print()
print("=" * 60)
print("CONTEXT (چیزی که به LLM داده می‌شه)")
print("=" * 60)
print(build_context(results))