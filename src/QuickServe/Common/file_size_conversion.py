def convert_size(size: int, precision: int = 2) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if size < 1024 or unit == "PB":
            return f"{size:.{precision}f} {unit}"
        size /= 1024
