import os
import re
import html


def ReadData(DATA):
    for filename in sorted(os.listdir(DATA)):
        if not filename.endswith('.sgm'):
            continue

        full_path = os.path.join(DATA, filename)

        with open(full_path, 'r', encoding='latin-1') as f:
            content = f.read()

        articles = re.findall(r'<REUTERS\b.*?</REUTERS>', content, re.DOTALL)
        for article in articles:
            newid_match = re.search(
                r'<REUTERS\b[^>]*\bNEWID="(\d+)"', article
            )
            if not newid_match:
                raise ValueError(f"Reuters article in {filename} has no NEWID")
            newid = int(newid_match.group(1))

            title_match = re.search(r'<TITLE>(.*?)</TITLE>', article, re.DOTALL)
            title = html.unescape(title_match.group(1).strip()) if title_match else ''

            body_match = re.search(r'<BODY>(.*?)</BODY>', article, re.DOTALL)
            body = html.unescape(body_match.group(1).strip()) if body_match else ''
            yield (newid, title + ' ' + body)
