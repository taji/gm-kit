"""Token preflight utility for large document handling (FR-015)."""

import os

DEFAULT_TOKEN_THRESHOLD = 100000  # 100K tokens
TOKENS_PER_CHAR = 4  # ~4 characters per token heuristic


def estimate_tokens(text: str) -> int:
    """Estimate token count from text length.

    Uses the heuristic: ~4 characters per token.

    Args:
        text: Input text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // TOKENS_PER_CHAR


def check_token_threshold(
    text: str, threshold: int | None = None, auto_proceed: bool = False
) -> dict[str, int | bool | str | None]:
    """Check if text exceeds token threshold and handle user decision.

    Args:
        text: Text to check (typically full markdown document)
        threshold: Token threshold (defaults to GM_TOKEN_THRESHOLD env var or 100000)
        auto_proceed: If True, skip interactive prompt (for --yes mode)

    Returns:
        Dictionary with:
            - estimated_tokens: int
            - exceeds_threshold: bool
            - user_choice: str ('proceed', 'skip', 'auto_proceed')
            - warning_message: str (if applicable)
    """
    if threshold is None:
        threshold = int(os.environ.get("GM_TOKEN_THRESHOLD", DEFAULT_TOKEN_THRESHOLD))

    estimated = estimate_tokens(text)
    exceeds = estimated > threshold

    result: dict[str, int | bool | str | None] = {
        "estimated_tokens": estimated,
        "threshold": threshold,
        "exceeds_threshold": exceeds,
        "user_choice": None,
        "warning_message": None,
    }

    if not exceeds:
        result["user_choice"] = "proceed"
        return result

    # Build warning message
    pages_estimate = estimated // 800  # Rough estimate: ~800 tokens per 2-column page
    warning = (
        f"WARNING: Document size ({estimated:,} estimated tokens, ~{pages_estimate} pages) "
        f"exceeds threshold ({threshold:,}).\n\n"
        f"Quality assessment accuracy may degrade for:\n"
        f"  - Heading hierarchy detection\n"
        f"  - TOC alignment validation\n\n"
    )
    result["warning_message"] = warning

    if auto_proceed:
        result["user_choice"] = "auto_proceed"
        return result

    # Interactive mode
    print(warning)
    response = input("Continue with quality assessment? [Y/n]: ").strip().lower()

    if response in ("", "y", "yes"):
        result["user_choice"] = "proceed"
    else:
        result["user_choice"] = "skip"

    return result


def format_token_info(estimated: int, threshold: int) -> str:
    """Format token information for display.

    Args:
        estimated: Estimated token count
        threshold: Token threshold

    Returns:
        Formatted string with token information
    """
    return (
        f"Token estimate: {estimated:,} / {threshold:,} "
        f"({estimated / threshold * 100:.1f}% of threshold)"
    )
