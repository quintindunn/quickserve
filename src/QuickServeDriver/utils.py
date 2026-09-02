import re


def sanitize_filename(string: str) -> str:
    """
    Converts a string to a sanitized filename.
    :param string: The input filename
    :return: a sanitize filename.
    """
    replacement_pattern = re.compile(r"[^a-zA-Z0-9-_]")

    return re.sub(replacement_pattern, "_", string)[:250]
