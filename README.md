# Mizan (ميزان)

Find the Moroccan law that answers your question, quoted word for word from the official text. Ask in Arabic, French, Darija or Arabizi.

**Live:** https://mizan-law-eta.vercel.app

Mizan does not write legal answers. It finds articles, quotes them exactly as the Ministry of Justice publishes them, and links each quote to its page in the official PDF. When nothing is close enough, it says so instead of guessing. It is a research tool, not legal advice.

## What it does

- **Ask.** "طردوني من الخدمة بلا سبب", "moul dar bgha ykhrjni", "licenciement abusif indemnité" or "المادة 53 من مدونة الأسرة" all lead to the articles that apply.
- **Read a law.** 50 laws and codes, article by article, with a filter inside each law.
- **Search all official documents.** 8,226 laws, decrees, circulars, conventions and royal speeches, by title.
- **See how current a text is.** Each law shows its consolidation date. The labour code's Arabic is consolidated to July 2026 and its French only to October 2011, so the page warns you.
- **Follow the Bulletin Officiel, compare two versions of a text, and screen a contract** for a few clauses that the law forbids.

Your questions are not stored. The app only counts them by language and field of law.

## Where the text comes from

Everything comes from [adala.justice.gov.ma](https://adala.justice.gov.ma), the Ministry of Justice portal.

| Step | Tool | Result |
|---|---|---|
| List the documents | `tools/crawl_adala.py` | `data/adala_catalog.json` |
| Download the chosen laws | `tools/download_core.py` | `data/adala_cache/` (not committed) |
| Cut into articles and index | `tools/build_corpus.py` | `data/corpus.sqlite`, `data/corpus_report.json` |

The Arabic PDFs store their text in a broken order: "المادة" can arrive as "ملا ادة". `src/pdf_articles.py` rebuilds each line from where the glyphs sit on the page, with no dictionary and no guessing. Footnotes, page numbers and cross-references that wrap onto their own line are kept out of the articles.

The family code comes out whole at 400 of 400 articles and the labour code at 589 of 589. Gaps in other laws' numbering are listed in `data/corpus_report.json`. Many are repealed articles, but they have not all been checked by a person.

**Not covered yet:** the General Tax Code, which the portal does not publish as one document, and most decrees, which are searchable by title only.

## How search works

1. A named article ("الفصل 540 من القانون الجنائي") is looked up directly.
2. `data/legal_index.json` is the index at the back of a law book: common questions and the articles that answer them, chosen by reading those articles.
3. `data/lexicon.json` maps Darija and everyday words to statutory ones, so "الخدمة" reaches "الشغل" and "راجلي" reaches "الزوج".
4. BM25 over stemmed Arabic and French, in SQLite FTS5, ranks everything else.

### How good it is

Measured with `tools/eval_retrieval.py` and the sets in `data/eval/`. "Hit" means the right article is in the first 5 results.

| Question set | Questions | Hit | How to read it |
|---|---|---|---|
| Tuning (`gold.json`) | 142 | 99% | The index was written against these, so this mostly proves nothing broke |
| Held-out (`heldout.json`) | 41 | 98% | Read before the index was written, so optimistic |
| First blind (`blind.json`) | 36 | 97% now, 50% when first measured | Used for tuning since, so only the 50% says anything |
| Second blind (`blind2.json`) | 34 | **68%** | The honest number: written before the last round of work and not tuned on |

On the second blind set, the right law came first for 71% of questions. Common questions do well. Rare ones and free-form Darija often miss, and some get no answer at all. A lawyer has not reviewed these sets yet ([#4](https://github.com/Bosaj/moroccan-law-ai/issues/4)).

Dense embeddings were tried too (multilingual MiniLM). Alone they reached 35%, and Darija only 5%. Combined with the older lexical search they reached 66% against that search's 58%. That gain did not justify shipping about 300 MB of runtime, so they are not used.

## Run it

The server needs Python 3.10+ and nothing else. The corpus is committed.

```bash
cd web && npm ci && npm run build && cd ..
```

```bash
python server.py
```

Then open http://localhost:8090.

```bash
pip install pytest && pytest
```

```bash
cd web && npm test
```

To rebuild the corpus from the official PDFs:

```bash
pip install -r requirements-tools.txt
```

```bash
python tools/crawl_adala.py && python tools/download_core.py && python tools/build_corpus.py
```

## API

| Route | What it returns |
|---|---|
| `GET /api/health` | Counts and corpus date |
| `POST /api/query` `{query, lang}` | Matching articles, each with its source links |
| `GET /api/laws` | The 50 laws |
| `GET /api/law?law=family&lang=ar` | One law's articles |
| `GET /api/article?law=family&number=53` | One article, in both languages where available |
| `GET /api/catalog?q=...` | Official documents by title |
| `GET /api/bo-issues`, `POST /api/bo-diff`, `POST /api/audit-contract` | Gazette index, text comparison, contract screening |

## Deployment

Vercel serves `web/dist` and runs `api/index.py`, which reuses `server.py`. See `vercel.json`.

## Licence

Proprietary, all rights reserved. See [LICENSE](LICENSE). The legal texts themselves belong to the public record.

Author: Oussama Elhadji ([@Bosaj](https://github.com/Bosaj))
