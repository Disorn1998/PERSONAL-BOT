"""Token budget fitting."""

from __future__ import annotations

from persona_bot.budget import estimate_tokens, fit_prompt, total_tokens


def test_estimate_tokens_nonzero() -> None:
    assert estimate_tokens("hello") >= 1
    assert estimate_tokens("") == 0


def test_fit_prompt_keeps_system_and_latest() -> None:
    messages = [{"role": "system", "content": "SYS"}]
    for i in range(40):
        messages.append({"role": "user", "content": f"u{i} " + ("x" * 200)})
        messages.append({"role": "assistant", "content": f"a{i} " + ("y" * 200)})
    messages.append({"role": "user", "content": "LATEST_QUESTION"})
    fitted = fit_prompt(messages, context_window=800, reply_reserve=100)
    assert fitted[0]["role"] == "system"
    latest = fitted[-1]["content"]
    assert latest.endswith("LATEST_QUESTION") or "LATEST_QUESTION" in latest
    assert total_tokens(fitted) <= 800 - 100 + 50  # small slack for rounding


def test_fit_prompt_empty_and_truncates_oversized_latest() -> None:
    assert fit_prompt([]) == []
    system_only = fit_prompt(
        [{"role": "system", "content": "SYS"}],
        context_window=100,
        reply_reserve=50,
    )
    assert system_only == [{"role": "system", "content": "SYS"}]
    huge = "Q" * 5000
    fitted = fit_prompt(
        [
            {"role": "system", "content": "SYS"},
            {"role": "user", "content": huge},
        ],
        context_window=400,
        reply_reserve=100,
    )
    assert fitted[0]["role"] == "system"
    assert fitted[-1]["role"] == "user"
    assert fitted[-1]["content"].startswith("…\n")
    assert len(fitted[-1]["content"]) < len(huge)
