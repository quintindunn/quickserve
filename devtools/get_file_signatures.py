"""
Generates the list of file signatures for SimpleFS

Author: Quintin Dunn
Date: 10/21/2026

Credit: https://en.wikipedia.org/wiki/List_of_file_signatures
"""

import re
from typing import Any, Generator

from bs4 import BeautifulSoup, PageElement
import requests

MANUALLY_ADDED_SIGNATURES = ["504B0304", "504B0506", "504B0508"]


def get_page_table() -> PageElement:
    url = "https://en.wikipedia.org/wiki/List_of_file_signatures"

    request = requests.get(
        url, headers={"User-Agent": "QuickServe (github.com/QuickServe/QuickServe)"}
    )

    soup = BeautifulSoup(request.content, "html.parser")

    table = soup.find("table", {"class": "wikitable sortable"})

    if not table:
        raise RuntimeError(f"Could not find table in {url}")

    return table


def is_hex_data(data: str) -> bool:
    segments = data.upper().split(" ")
    pattern = re.compile("[0-9A-F]{2}")
    return all(pattern.match(segment) for segment in segments)


def get_file_signatures() -> Generator[str, Any, None]:
    table = get_page_table()

    head = table.find_next("th")
    if not head:
        raise RuntimeError(f"Could not find table head")

    anchor = head.find_next("a", {"href": "https://en.wikipedia.org/wiki/Hexadecimal"})
    if not anchor:
        raise RuntimeError("Table has changed!")

    for k, row in enumerate(table.find_all_next("tr")):
        if k == 0:
            continue

        hex_code = row.find_next("td")
        if not hex_code:
            raise RuntimeError(f"Could not find hexadecimal code in {row}")

        text = hex_code.text.upper().strip()
        is_hex = is_hex_data(hex_code.text)
        if not is_hex:
            continue

        text = text.replace("\xa0", "").replace(" ", "")
        yield text

    for added in MANUALLY_ADDED_SIGNATURES:
        yield added


def build_python_file():
    with open("file_signatures.py", "w") as f:
        f.write("# SOURCE: https://en.wikipedia.org/wiki/List_of_file_signatures\n")
        f.write("# Generated with devtools/get_file_signatures.py\n")

        sig_list = (
            f"SIGNATURES: list[str] = ["
            + "".join(['"' + i + '",' for i in get_file_signatures()])
            + "]"
        )
        f.write(sig_list)


if __name__ == "__main__":
    build_python_file()
