# Moroccan Law AI

> A legal-Q&A assistant that actually understands Moroccan law and answers with citations to the real article/text.

**Status:** pre-alpha scaffold (no code yet). **Feasibility rating:** 8/10 — real gap; legally sensitive.
**Author:** Oussama EL HADJI. Part of the Bosaj ideas portfolio (sibling repo: `dual_portfolio_hub`).

---

## Problem

Legal AI tools are concentrated on US/EU law. Moroccans asking everyday legal questions (labour, rent, family, administrative) have no grounded, source-cited assistant in Arabic / Darija / French.

## Why build it (gap analysis)

General legal chatbots exist, but a dedicated model grounded in the Moroccan legal corpus does not. This is open ground — but it is legally sensitive and must cite sources, never invent articles, and always disclaim that it is not legal advice.

## Prior art & open bases to fork

- [DarijaBERT](https://huggingface.co/SI2M-Lab/DarijaBERT) — First BERT for Moroccan Arabic — good for retrieval/embeddings.
- [Atlas-Chat-2B / 9B](https://huggingface.co/MBZUAI-Paris/Atlas-Chat-2B) — Darija instruction-tuned chat — strong Q&A base.
- [Al-Atlas pretraining](https://github.com/atlasia-ma/Al-Atlas-Moroccan-Darija-Pretraining) — Full Darija pretraining pipeline.
- [LLM-Finetuned-Morocco-Darija](https://github.com/BounharAbdelaziz/LLM-Finetuned-Morocco-Darija) — Llama-2 Darija fine-tuning code.
- [Moroccan Darija LLMs collection](https://huggingface.co/collections/BounharAbdelaziz/moroccan-darija-llms) — Index of Darija models + datasets.

## Proposed architecture

1. Ingest the legal corpus (codes, Bulletin Officiel) → clean → chunk by article.
2. Index chunks (keyword + embeddings).
3. On a question: retrieve the relevant articles, build a grounded prompt, generate an answer that quotes and links the exact articles.
4. Verification layer: reject / flag any answer whose cited article is not in the retrieved set (anti-hallucination).
5. Human-in-the-loop: a lawyer reviews a sample before anything is called production-ready.

## Tech stack (proposed)

- RAG over a Moroccan legal corpus (codes + Bulletin Officiel) — grounding beats fine-tuning for correctness
- Retrieval: BM25 + multilingual embeddings (fused, like dual_portfolio_hub)
- Generation: Atlas-Chat / a fine-tuned Darija-AR-FR model
- Mandatory article citations + "not legal advice" disclaimer on every answer
- Python: FastAPI backend, a vector store, an eval harness

## Roadmap

- v0.1 — collect an open legal corpus + RAG prototype (French first).
- v0.2 — add Arabic + Darija retrieval and answers.
- v0.3 — fine-tune a Darija model on legal Q&A.
- v0.4 — citation-verification layer + evaluation set reviewed by a lawyer.

---

## For LLM agents & contributors continuing this project

This repo is a **scaffold**: README + standard files, no implementation yet. If you are an AI agent asked to "continue developing", read this section first.

- Do NOT build an ungrounded LLM wrapper. Correctness here has legal consequences: every claim must cite a retrieved article, and the system must refuse rather than guess.
- Sourcing the corpus legally is the first blocker — identify which Moroccan legal texts are public-domain / redistributable before training. Record provenance per document.
- Reuse the hybrid-RAG approach from the sibling repo dual_portfolio_hub (api/_lib/knowledge.js): BM25 + embeddings fused by Reciprocal Rank Fusion.
- Always output a disclaimer: this is informational, not legal advice.

**Ground rules:** keep this README in sync with reality as you build; prefer forking/reusing the bases above over greenfield code; write tests for anything correctness-critical; never commit secrets (see `.gitignore`); follow Conventional Commits (see `CONTRIBUTING.md`).

## Getting started

```bash
# nothing to run yet — this is a scaffold.
# python -m venv .venv && pip install -r requirements.txt   # once code lands
```

## License

[MIT](LICENSE) — © 2026 Oussama EL HADJI
