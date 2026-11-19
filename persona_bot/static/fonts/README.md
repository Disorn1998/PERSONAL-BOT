# Bundled UI fonts

Self-hosted **SIL Open Font License (OFL) 1.1** faces for offline Streamlit CSS.
No CDN / Google Fonts network calls at runtime.

| File | Family | Role | Upstream |
|---|---|---|---|
| `Inter-Regular.woff2` / `Inter-SemiBold.woff2` | Inter | Latin UI body / emphasis | [rsms/inter](https://github.com/rsms/inter) (via `@fontsource/inter@5.2.5` latin subsets) |
| `NotoSansThai-Regular.woff2` / `NotoSansThai-Bold.woff2` | Noto Sans Thai | Thai UI glyphs | [notofonts/thai](https://github.com/notofonts/thai) (via `@fontsource/noto-sans-thai@5.2.5` thai subsets) |
| `OFL-Inter.txt` | — | Licence text | Inter `LICENSE.txt` |
| `OFL-NotoSansThai.txt` | — | Licence text | google/fonts `ofl/notosansthai/OFL.txt` |

`persona_bot/ui/theme.py` embeds these as `data:` URIs in `@font-face` (Streamlit has no public static-file mount for package assets).

See also root `THIRD_PARTY_NOTICES.md`.
