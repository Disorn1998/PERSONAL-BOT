"""CLI entry point for persona-bot — launches the Streamlit shell."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Run the Streamlit UI (``persona-bot`` console script)."""
    app_path = Path(__file__).resolve().parent / "main.py"
    # Avoid importing streamlit.web at module import time for unit tests.
    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
    ]
    raise SystemExit(stcli.main())


if __name__ == "__main__":
    main()
