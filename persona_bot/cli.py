"""CLI entry point for persona-bot — launches Streamlit from any cwd."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    """Return repository / install root that contains ``persona_bot/main.py`` and pyproject."""
    here = Path(__file__).resolve().parent
    # Editable/src layout: <root>/persona_bot/cli.py
    candidate = here.parent
    if (candidate / "persona_bot" / "main.py").exists():
        return candidate
    # Fallback: cwd if it looks like the project
    cwd = Path.cwd()
    if (cwd / "persona_bot" / "main.py").exists():
        return cwd
    return candidate


def main() -> None:
    """Run the Streamlit UI (``persona-bot`` console script)."""
    root = project_root()
    os.chdir(root)
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    app_path = root / "persona_bot" / "main.py"
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
