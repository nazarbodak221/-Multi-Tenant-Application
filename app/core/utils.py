from datetime import datetime
from typing import Optional


def format_datetime(
    dt: Optional[datetime], format: str = "%Y-%m-%d %H:%M:%S"
) -> Optional[str]:
    """
    Format datetime to readable string format

    Args:
        dt: Datetime object to format
        format: Format string (default: "YYYY-MM-DD HH:MM:SS")

    Returns:
        Formatted datetime string or None if dt is None
    """
    if dt is None:
        return None
    return dt.strftime(format)


def format_date(dt: Optional[datetime], format: str = "%Y-%m-%d") -> Optional[str]:
    """
    Format datetime to date string

    Args:
        dt: Datetime object to format
        format: Format string (default: "YYYY-MM-DD")

    Returns:
        Formatted date string or None if dt is None
    """
    if dt is None:
        return None
    return dt.strftime(format)
