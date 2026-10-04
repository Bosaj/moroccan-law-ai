# 2. Roadmap

- v0.1 — collect an open legal corpus + RAG prototype (French first).
- v0.2 — add Arabic + Darija retrieval and answers.
- v0.3 — fine-tune a Darija model on legal Q&A.
- v0.4 — citation-verification layer + evaluation set reviewed by a lawyer.

## Notes for contributors / LLM agents
- Do NOT build an ungrounded LLM wrapper. Correctness here has legal consequences: every claim must cite a retrieved article, and the system must refuse rather than guess.
- Sourcing the corpus legally is the first blocker — identify which Moroccan legal texts are public-domain / redistributable before training. Record provenance per document.
- Reuse the hybrid-RAG approach from the sibling repo dual_portfolio_hub (api/_lib/knowledge.js): BM25 + embeddings fused by Reciprocal Rank Fusion.
- Always output a disclaimer: this is informational, not legal advice.
