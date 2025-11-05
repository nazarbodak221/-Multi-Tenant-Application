from datetime import datetime


def format_datetime(
    dt: datetime | None, format: str = "%Y-%m-%d %H:%M:%S"
) -> str | None:
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


def format_date(dt: datetime | None, format: str = "%Y-%m-%d") -> str | None:
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
