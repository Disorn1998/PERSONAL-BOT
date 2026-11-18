# Third-party notices

Python dependencies are declared in `pyproject.toml` / `uv.lock` and carry their
own licences (typically MIT, Apache-2.0, or BSD). Review each package before
redistribution.

## UI fonts

- Status: **not bundled yet** (Streamlit / system sans-serif).
- When fonts are added under `app/static/fonts/`, list family, source URL, and
  licence file path here.

## Embedding models (fastembed / ONNX) — licence table

Downloaded at first use into the local cache (`HF_HOME` / `FASTEMBED_CACHE_PATH`).
**Not redistributed in this git repo.** Verify upstream licence before commercial redistribution.

| Preset | Model id | Upstream | Licence (verify) |
|---|---|---|---|
| `lite` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Hugging Face | Apache-2.0 **TODO(verify)** on model card |
| `multilingual` | `intfloat/multilingual-e5-large` | Hugging Face | MIT **TODO(verify)** on model card |
| `quality` | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | Hugging Face | Apache-2.0 **TODO(verify)** on model card |

Sources to re-check periodically:

- https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- https://huggingface.co/intfloat/multilingual-e5-large
- https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2

## Groq models

Model weights are hosted by Groq; this project only sends chat requests with the
user's BYOK key. Model IDs come from `.env` / `.env.example` — never hardcoded
in Python. Terms: https://groq.com

## Other runtime components

| Component | Role | Notes |
|---|---|---|
| ChromaDB | Local vector store under `data/chroma/` | Apache-2.0 upstream |
| Streamlit | Chat UI | Apache-2.0 upstream |
| OpenAI Python SDK | Groq OpenAI-compatible client | Apache-2.0 upstream |
