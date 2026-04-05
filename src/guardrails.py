"""Guardrails for the Bank Assistant.

Goals:
- block / redact PII in user inputs
- block harmful / policy-violating requests
- keep the assistant on-topic (NUST Bank products/services)

This is intentionally lightweight (regex-based) to stay within project scope.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("cnic", re.compile(r"\b\d{5}-\d{7}-\d\b")),
    ("phone", re.compile(r"\b(?:\+?92|0)\d{10}\b")),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    # simplistic card pattern (do NOT over-block random numbers)
    ("card", re.compile(r"\b(?:\d[ -]*?){13,19}\b")),
]

HARMFUL_INTENT = re.compile(
    r"\b(?:how to (?:hack|steal)|bypass|carding|phishing|ddos|malware|make a bomb|kill)\b",
    re.IGNORECASE,
)


@dataclass
class GuardrailResult:
    allowed: bool
    message: str | None = None
    sanitized_text: str | None = None
    flags: list[str] | None = None


def redact_pii(text: str) -> tuple[str, list[str]]:
    flags: list[str] = []
    redacted = text
    for name, pat in PII_PATTERNS:
        if pat.search(redacted):
            flags.append(name)
            redacted = pat.sub(f"<{name.upper()}_REDACTED>", redacted)
    return redacted, flags


def check_input(text: str) -> GuardrailResult:
    if not text or not text.strip():
        return GuardrailResult(allowed=False, message="Please enter a question.")

    if HARMFUL_INTENT.search(text):
        return GuardrailResult(
            allowed=False,
            message="Sorry, I can't help with that. I can assist with NUST Bank products and services.",
            flags=["harmful_intent"],
        )

    sanitized, pii_flags = redact_pii(text)
    if pii_flags:
        return GuardrailResult(
            allowed=True,
            sanitized_text=sanitized,
            flags=[f"pii:{f}" for f in pii_flags],
            message=None,
        )

    return GuardrailResult(allowed=True, sanitized_text=text, flags=[])


def check_output(text: str) -> GuardrailResult:
    # Prevent accidental PII echoing.
    sanitized, pii_flags = redact_pii(text)
    if pii_flags:
        return GuardrailResult(
            allowed=True,
            sanitized_text=sanitized,
            flags=[f"pii:{f}" for f in pii_flags],
        )
    return GuardrailResult(allowed=True, sanitized_text=text, flags=[])
