from __future__ import annotations

from enum import Enum
import re


class MemoryPolicyDecision(str, Enum):
    """Minimal write-policy outcome for durable memory writes."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRES_CONFIRMATION = "requires_confirmation"


SECRET_PATTERN_LABELS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "secrets/credentials",
        re.compile(
            r"(?i)\b(api[_ -]?key|api[_ -]?token|access[_ -]?token|auth[_ -]?token|secret|password|passwd|session[_ -]?cookie)\b\s*[:=]"
        ),
    ),
    ("secrets/credentials", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_.-]{8,}\b")),
    ("secrets/credentials", re.compile(r"\bsk-[A-Za-z0-9_.-]{8,}\b")),
    ("secrets/credentials", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("secrets/credentials", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)

DENY_PATTERN_LABELS: tuple[tuple[str, re.Pattern[str]], ...] = (
    *SECRET_PATTERN_LABELS,
    ("seed phrase", re.compile(r"(?i)\b(seed phrase|mnemonic phrase|recovery phrase)\b\s*[:=]")),
    (
        "raw transcript",
        re.compile(
            r"(?im)^\s*(user|assistant|system|tool)\s*:\s+.*$[\s\S]*^\s*(user|assistant|system|tool)\s*:\s+"
        ),
    ),
    (
        "temporary task status",
        re.compile(
            r"(?i)\b(PR|issue)\s*#\d+\b|\bcommit\s+[0-9a-f]{7,40}\b|\bphase\s+\d+\s+(done|complete)|\bt_[0-9a-f]{8}\b"
        ),
    ),
)

CONFIRMATION_PATTERN_LABELS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("raw email address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("private phone number", re.compile(r"(?<![\w-])(?:\+\d{1,3}[ .()-]?)?(?:\(?\d{3}\)?[ .()-]?){2}\d{4}(?![\w-])")),
    (
        "third-party private data",
        re.compile(r"(?i)\b[A-Z][a-z]+(?:'s|’s)\s+(private\s+)?(phone|email|address|medical|salary|password|secret)\b"),
    ),
)

ALLOW_HINTS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\b(user preference|project convention|workflow|verified|procedure|run\s+uv\s+run)\b"),
    re.compile(r"用户偏好|项目约定|工作流|流程|经验证|可复用"),
)


def memory_policy_matches(content: str) -> tuple[MemoryPolicyDecision, list[str]]:
    """Classify content against the minimal durable-memory write policy."""

    stripped = content.strip()
    if not stripped:
        return MemoryPolicyDecision.DENY, ["empty content"]

    deny_labels = _matching_labels(stripped, DENY_PATTERN_LABELS)
    if deny_labels:
        return MemoryPolicyDecision.DENY, deny_labels

    confirmation_labels = _matching_labels(stripped, CONFIRMATION_PATTERN_LABELS)
    if confirmation_labels:
        return MemoryPolicyDecision.REQUIRES_CONFIRMATION, confirmation_labels

    # The default allow boundary is intentionally narrow but practical: compact
    # durable facts/procedures that do not match deny/confirmation categories.
    # ALLOW_HINTS documents the preferred shape without blocking existing SDK use.
    return MemoryPolicyDecision.ALLOW, []


def evaluate_memory_write_policy(content: str) -> MemoryPolicyDecision:
    """Return the allow/deny/confirmation decision for a candidate memory."""

    decision, _labels = memory_policy_matches(content)
    return decision


def memory_policy_violations(content: str) -> list[str]:
    """Return deny/confirmation labels that block automatic memory writes."""

    decision, labels = memory_policy_matches(content)
    if decision == MemoryPolicyDecision.ALLOW:
        return []
    return labels


def ensure_memory_content_allowed(content: str, *, confirmed_by_user: bool = False) -> None:
    """Refuse high-risk memory writes unless the policy explicitly allows them."""

    decision, labels = memory_policy_matches(content)
    if decision == MemoryPolicyDecision.ALLOW:
        return
    joined = ", ".join(dict.fromkeys(labels))
    if decision == MemoryPolicyDecision.REQUIRES_CONFIRMATION and confirmed_by_user:
        return
    if decision == MemoryPolicyDecision.REQUIRES_CONFIRMATION:
        raise ValueError(f"memory write requires user confirmation: {joined}")
    raise ValueError(f"refusing to store high-risk memory: {joined}")


def _matching_labels(content: str, patterns: tuple[tuple[str, re.Pattern[str]], ...]) -> list[str]:
    return [label for label, pattern in patterns if pattern.search(content)]
