# 1. Architecture

1. Ingest the legal corpus (codes, Bulletin Officiel) → clean → chunk by article.
2. Index chunks (keyword + embeddings).
3. On a question: retrieve the relevant articles, build a grounded prompt, generate an answer that quotes and links the exact articles.
4. Verification layer: reject / flag any answer whose cited article is not in the retrieved set (anti-hallucination).
5. Human-in-the-loop: a lawyer reviews a sample before anything is called production-ready.

## Proposed stack
- RAG over a Moroccan legal corpus (codes + Bulletin Officiel) — grounding beats fine-tuning for correctness
- Retrieval: BM25 + multilingual embeddings (fused, like dual_portfolio_hub)
- Generation: Atlas-Chat / a fine-tuned Darija-AR-FR model
- Mandatory article citations + "not legal advice" disclaimer on every answer
- Python: FastAPI backend, a vector store, an eval harness

## Open bases to fork
- [DarijaBERT](https://huggingface.co/SI2M-Lab/DarijaBERT) — First BERT for Moroccan Arabic — good for retrieval/embeddings.
- [Atlas-Chat-2B / 9B](https://huggingface.co/MBZUAI-Paris/Atlas-Chat-2B) — Darija instruction-tuned chat — strong Q&A base.
- [Al-Atlas pretraining](https://github.com/atlasia-ma/Al-Atlas-Moroccan-Darija-Pretraining) — Full Darija pretraining pipeline.
- [LLM-Finetuned-Morocco-Darija](https://github.com/BounharAbdelaziz/LLM-Finetuned-Morocco-Darija) — Llama-2 Darija fine-tuning code.
- [Moroccan Darija LLMs collection](https://huggingface.co/collections/BounharAbdelaziz/moroccan-darija-llms) — Index of Darija models + datasets.
