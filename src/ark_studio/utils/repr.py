# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License


def format_size(size: int, *, ndigits: int = 2, suffix: str = "") -> str:
    """Formats file size to human readable format.

    Args:
        size: Size in bytes
        ndigits: Number of decimal places
        suffix: Additional suffix to append after unit (e.g. "/s" for speed)

    Returns:
        Formatted size string
    """
    if size < 0:
        return f"-{format_size(-size, ndigits=ndigits, suffix=suffix)}"

    size_float = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_float < 1024.0:
            return f"{size_float:.{ndigits}f} {unit}{suffix}"
        size_float /= 1024.0
    return f"{size_float:.{ndigits}f} PB{suffix}"


__all__ = ["format_size"]
