from __future__ import annotations
from pathlib import Path
import re
import fitz

root = Path('/home/todd/Dev/gm-kit')
input_pdf = root / 'temp-resources/conversions/call-of-cthulhu/codex/preprocessed/call-of-cthulhu-no-images-delete.pdf'
output_md = root / 'temp-resources/conversions/call-of-cthulhu/codex/call-of-cthulhu-full.md'


def normalize_bullets(line: str) -> str:
    line = line.replace('•', '- ')
    line = re.sub(r'^\s*[-\u2022]\s*', '- ', line)
    return line


def is_all_caps(line: str) -> bool:
    letters = [c for c in line if c.isalpha()]
    if not letters:
        return False
    return all(c.isupper() for c in letters)


def is_title_case(line: str) -> bool:
    words = [w for w in re.split(r'\s+', line.strip()) if w]
    if len(words) < 2:
        return False
    cap = 0
    for w in words:
        if w[0].isupper():
            cap += 1
    return cap / len(words) > 0.7


with fitz.open(input_pdf) as doc:
    pages = []
    for page in doc:
        text = page.get_text('text')
        lines = [ln.rstrip() for ln in text.splitlines()]
        cleaned = []
        for ln in lines:
            s = ln.strip()
            if not s:
                cleaned.append('')
                continue
            if s.isdigit():
                continue
            s = normalize_bullets(s)
            cleaned.append(s)
        pages.append('\n'.join(cleaned))

raw = '\n\n'.join(pages)

out_lines = []
for ln in raw.splitlines():
    s = ln.strip()
    if not s:
        out_lines.append('')
        continue
    if is_all_caps(s) and len(s) <= 80:
        out_lines.append(f"## {s.title()}")
        continue
    if is_title_case(s) and len(s) <= 80:
        out_lines.append(f"### {s}")
        continue
    out_lines.append(s)

full_text = '\n'.join(out_lines)

# fix hyphenation across line breaks
full_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', full_text)

# normalize line breaks within paragraphs
lines = full_text.splitlines()
merged = []
for i, line in enumerate(lines):
    s = line.rstrip()
    if not s:
        merged.append('')
        continue
    if s.startswith('#') or s.startswith('- ') or s.startswith('>'):
        merged.append(s)
        continue
    if i + 1 < len(lines) and lines[i + 1].strip() == '':
        merged.append(s)
        continue
    if merged and merged[-1] and not merged[-1].startswith(('#', '- ', '>')):
        merged[-1] = merged[-1] + ' ' + s
    else:
        merged.append(s)

full_text = '\n'.join(merged)
full_text = re.sub(r'\n{3,}', '\n\n', full_text)

output_md.write_text(full_text, encoding='utf-8')
print(f"Wrote markdown to {output_md}")
