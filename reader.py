import html
import os
import re


def ReadData(DATA):
    for filename in sorted(os.listdir(DATA)):
        if not filename.endswith(".sgm"):
            
            continue

        path = os.path.join(DATA, filename)

        with open(path, "r", encoding="latin-1") as source:
            data = source.read()


        articles = re.findall(r'<REUTERS\b.*?</REUTERS>', data, re.DOTALL)
        for article in articles:
            match = re.search(
                r'<REUTERS\b[^>]*\bNEWID="(\d+)"', article
            )
            if not match:
                raise ValueError(f"Reuters article in {filename} has no NEWID")
            doc_id = int(match.group(1))

            title_match = re.search(r'<TITLE>(.*?)</TITLE>', article, re.DOTALL)
            title = html.unescape(title_match.group(1).strip()) if title_match else ""

            body_match = re.search(r'<BODY>(.*?)</BODY>', article, re.DOTALL)
            body = html.unescape(body_match.group(1).strip()) if body_match else ""
            yield doc_id, title + " " + body
