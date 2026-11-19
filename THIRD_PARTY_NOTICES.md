# Third-party notices

Python dependencies are declared in `pyproject.toml` / `uv.lock` and carry their
own licences (typically MIT, Apache-2.0, or BSD). Review each package before
redistribution.

## UI fonts

Self-hosted under `persona_bot/static/fonts/` (OFL 1.1). Injected via
`persona_bot/ui/theme.py` as base64 `@font-face` data URIs — **no CDN** at runtime.

| Family | Files | Licence | Source |
|---|---|---|---|
| **Inter** | `Inter-Regular.woff2`, `Inter-SemiBold.woff2` | `OFL-Inter.txt` | [rsms/inter](https://github.com/rsms/inter) (latin subsets via `@fontsource/inter@5.2.5`) |
| **Noto Sans Thai** | `NotoSansThai-Regular.woff2`, `NotoSansThai-Bold.woff2` | `OFL-NotoSansThai.txt` | [notofonts/thai](https://github.com/notofonts/thai) (thai subsets via `@fontsource/noto-sans-thai@5.2.5`) |

See `persona_bot/static/fonts/README.md` for refresh notes.

## Embedding models (fastembed / ONNX) — licence table

Downloaded at first use into the local cache (`HF_HOME` / `FASTEMBED_CACHE_PATH`).
**Not redistributed in this git repo.** Verified against Hugging Face model cards
on **2026-11-18** (card `license` / `license:` tag). Re-check before commercial
redistribution of the downloaded weights.

| Preset | Model id | Upstream | Licence | Verified |
|---|---|---|---|---|
| `lite` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Hugging Face | **Apache-2.0** | Yes — card `license: apache-2.0` |
| `multilingual` | `intfloat/multilingual-e5-large` | Hugging Face | **MIT** | Yes — card `license: mit` |
| `quality` | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | Hugging Face | **Apache-2.0** | Yes — card `license: apache-2.0` |

Sources (re-check periodically):

- https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- https://huggingface.co/intfloat/multilingual-e5-large
- https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2

Notes:

- Apache-2.0 and MIT both allow local use with a BYOK app; keep upstream notices if you
  redistribute the weights themselves (this repo does not ship them).
- fastembed may resolve ONNX exports of the same model ids — treat the HF card licence
  as authoritative for the weights.

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
