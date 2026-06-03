"""Optional Claude enrichment layer.

The rules engine is fully deterministic and runs with no API key. When
ANTHROPIC_API_KEY is set, ``enrich`` asks Claude to tighten the customer-facing
explanation while keeping the rules engine's verdict authoritative. If the key
is absent or the call fails, the original analysis is returned unchanged.
"""
from __future__ import annotations

import os
from typing import Optional


def is_enabled() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def enrich(analysis: dict, model: Optional[str] = None) -> dict:
    if not is_enabled():
        return analysis
    try:
        import anthropic
    except Exception:
        return analysis

    model = model or os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6")
    try:
        client = anthropic.Anthropic()
        prompt = (
            "You are a senior 8x8 network support engineer. The rules engine produced this verdict:\n"
            f"- Health: {analysis['health']}\n- Root cause: {analysis['rootCause']}\n"
            f"- Region: {analysis['geo'].get('region')}\n"
            "Rewrite ONLY the customer-facing explanation in <=3 plain-English sentences. "
            "Do not change the technical verdict. Return just the sentences."
        )
        msg = client.messages.create(
            model=model, max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        if text:
            analysis = {**analysis, "customerText": text, "enrichedBy": model}
    except Exception:
        # Never let enrichment break the deterministic result.
        return analysis
    return analysis
