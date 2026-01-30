from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import json
import re
import fitz

root = Path('/home/todd/Dev/gm-kit')
work_dir = root / 'temp-resources/conversions/call-of-cthulhu/codex'
input_pdf = work_dir / 'preprocessed' / 'call-of-cthulhu-no-images-delete.pdf'
mapping_path = work_dir / 'font-family-mapping.json'

phase4_md = work_dir / 'call-of-cthulhu-phase4.md'
phase5_md = work_dir / 'call-of-cthulhu-phase5.md'
phase6_md = work_dir / 'call-of-cthulhu-phase6.md'


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


def normalize_heading_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_toc_line(line: str) -> str:
    cleaned = re.sub(r'[\x00-\x1f]', '', line)
    cleaned = cleaned.replace('�', '')
    if re.search(r'(\.{2,}|�|\x08)', line) and re.search(r'\d+$', line.strip()):
        cleaned = re.sub(r'[\.·•\-\s]{2,}(\d+)$', r' \1', cleaned)
    return cleaned


def is_mashed_toc_line(line: str, toc_titles: list[str]) -> bool:
    if len(re.findall(r'\d+', line)) < 5:
        return False
    hits = 0
    lower = line.lower()
    for title in toc_titles:
        if title.lower() in lower:
            hits += 1
        if hits >= 3:
            return True
    return False


def load_toc() -> list[tuple[int, str]]:
    toc_path = work_dir / 'toc-extracted.txt'
    if toc_path.exists():
        items: list[tuple[int, str]] = []
        for line in toc_path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 2:
                try:
                    level = int(parts[0])
                except ValueError:
                    continue
                title = parts[1]
                items.append((level, title))
        return items

    with fitz.open(input_pdf) as doc:
        toc = doc.get_toc()
    return [(lvl, title) for lvl, title, _ in toc]


LABEL_PRIORITY = {
    '#': 5,
    '##': 4,
    '###': 3,
    'gm_note': 3,
    'quote': 2,
    'quote_author': 2,
    'body': 1,
    '-': 0,
}


def load_mapping() -> tuple[dict[tuple[float, str], str], dict[tuple[float, str], dict[str, str]]]:
    if not mapping_path.exists():
        return {}, {}
    raw = json.loads(mapping_path.read_text(encoding='utf-8'))
    if isinstance(raw, dict):
        raw = raw.get('families', [])
    mapping: dict[tuple[float, str], str] = {}
    overrides: dict[tuple[float, str], dict[str, str]] = {}
    for item in raw:
        size = float(item.get('size', 0.0))
        font = str(item.get('font', '')).strip()
        label = str(item.get('label', '')).strip() or 'body'
        if label == '-':
            label = 'body'
        if not font:
            continue
        mapping[(size, font)] = label
        override_items = item.get('overrides', [])
        if isinstance(override_items, list):
            override_map: dict[str, str] = {}
            for override in override_items:
                text = str(override.get('text', '')).strip()
                if not text:
                    continue
                override_label = normalize_label(str(override.get('label', '')).strip())
                if not override_label:
                    continue
                override_map[normalize_heading_text(text)] = override_label
            if override_map:
                overrides[(size, font)] = override_map
    return mapping, overrides


def normalize_label(label: str | None) -> str | None:
    if not label:
        return None
    lowered = label.strip().lower()
    if lowered in {'x', 'drop', 'remove'}:
        return '-'
    if label.strip() == '-':
        return '-'
    return label.strip()


def build_line_label_map(pdf_path: Path) -> dict[str, str]:
    mapping, overrides = load_mapping()
    if not mapping:
        return {}
    mapping_by_font: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for (size, font), label in mapping.items():
        mapping_by_font[font].append((size, label))

    def resolve_label(size: float, font: str, text: str) -> str | None:
        size = round(size, 1)
        text_key = normalize_heading_text(text)
        override_map = overrides.get((size, font))
        if override_map and text_key in override_map:
            return normalize_label(override_map[text_key])
        label = mapping.get((size, font))
        if label is None:
            candidates = mapping_by_font.get(font, [])
            for candidate_size, candidate_label in candidates:
                if abs(candidate_size - size) <= 0.1:
                    label = candidate_label
                    break
        return normalize_label(label)

    line_label_map: dict[str, str] = {}
    with fitz.open(pdf_path) as doc:
        for page in doc:
            blocks = page.get_text('dict').get('blocks', [])
            for block in blocks:
                if block.get('type') != 0:
                    continue
                for line in block.get('lines', []):
                    spans = line.get('spans', [])
                    if not spans:
                        continue
                    text = ''.join(span.get('text', '') for span in spans).strip()
                    if not text:
                        continue
                    size_counts: dict[tuple[float, str], int] = {}
                    for span in spans:
                        font = span.get('font', '')
                        size = float(span.get('size', 0.0))
                        key = (round(size, 1), font)
                        size_counts[key] = size_counts.get(key, 0) + len(span.get('text', ''))
                    dominant_key = max(size_counts.items(), key=lambda item: item[1])[0]
                    label = resolve_label(dominant_key[0], dominant_key[1], text)
                    if not label:
                        continue
                    key = normalize_heading_text(text)
                    if not key:
                        continue
                    existing = line_label_map.get(key)
                    if existing is None:
                        line_label_map[key] = label
                        continue
                    if LABEL_PRIORITY.get(label, 0) > LABEL_PRIORITY.get(existing, 0):
                        line_label_map[key] = label
    return line_label_map


def build_heading_phrase_map(pdf_path: Path) -> dict[str, dict[str, str]]:
    mapping, overrides = load_mapping()
    if not mapping:
        return {}
    mapping_by_font: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for (size, font), label in mapping.items():
        mapping_by_font[font].append((size, label))

    def resolve_label(size: float, font: str, text: str) -> str | None:
        size = round(size, 1)
        text_key = normalize_heading_text(text)
        override_map = overrides.get((size, font))
        if override_map and text_key in override_map:
            return normalize_label(override_map[text_key])
        label = mapping.get((size, font))
        if label is None:
            candidates = mapping_by_font.get(font, [])
            for candidate_size, candidate_label in candidates:
                if abs(candidate_size - size) <= 0.1:
                    label = candidate_label
                    break
        return normalize_label(label)

    phrase_map: dict[str, dict[str, str]] = {}
    with fitz.open(pdf_path) as doc:
        for page in doc:
            blocks = page.get_text('dict').get('blocks', [])
            for block in blocks:
                if block.get('type') != 0:
                    continue
                for line in block.get('lines', []):
                    spans = line.get('spans', [])
                    if not spans:
                        continue
                    for span in spans:
                        text = span.get('text', '').strip()
                        if not text or len(text) < 3:
                            continue
                        if not any(c.isalpha() for c in text):
                            continue
                        label = resolve_label(float(span.get('size', 0.0)), span.get('font', ''), text)
                        if label not in {'#', '##', '###'}:
                            continue
                        key = normalize_heading_text(text)
                        if key and key not in phrase_map:
                            phrase_map[key] = {'label': label, 'text': text}
    return phrase_map


def build_toc_block() -> list[str]:
    toc_path = work_dir / 'toc-extracted.txt'
    lines: list[str] = []
    if toc_path.exists():
        for line in toc_path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                try:
                    level = int(parts[0])
                except ValueError:
                    continue
                title = parts[1]
                page = parts[2]
                indent = '  ' * max(level - 1, 0)
                lines.append(f"{indent}- {title} {page}")
        return lines

    toc_items = load_toc()
    for level, title in toc_items:
        indent = '  ' * max(level - 1, 0)
        lines.append(f"{indent}- {title}")
    return lines


# Phase 4: Text extraction
with fitz.open(input_pdf) as doc:
    total_pages = len(doc)
    headers: list[str] = []
    footers: list[str] = []
    page_texts: list[str] = []

    for page in doc:
        raw_lines = [ln.rstrip() for ln in page.get_text('text').splitlines()]
        clean_lines = [ln.strip() for ln in raw_lines if ln.strip()]
        if clean_lines:
            headers.append(clean_lines[0])
            footers.append(clean_lines[-1])

    # header/footer detection
    from collections import Counter

    header_counts = Counter(headers)
    footer_counts = Counter(footers)
    common_headers = {h for h, c in header_counts.items() if c >= total_pages * 0.5}
    common_footers = {f for f, c in footer_counts.items() if c >= total_pages * 0.5}

    for page in doc:
        lines = [ln.rstrip() for ln in page.get_text('text').splitlines()]
        cleaned: list[str] = []
        for ln in lines:
            s = ln.strip()
            if not s:
                cleaned.append('')
                continue
            if s.isdigit():
                continue
            if s in common_headers or s in common_footers:
                continue
            s = normalize_bullets(s)
            cleaned.append(s)
        page_texts.append('\n'.join(cleaned))

raw = '\n\n'.join(page_texts)

phase4_lines: list[str] = []
for ln in raw.splitlines():
    s = ln.strip()
    if not s:
        phase4_lines.append('')
        continue
    if is_all_caps(s) and len(s) <= 80:
        phase4_lines.append(f"## {s.title()}")
        continue
    if is_title_case(s) and len(s) <= 80:
        phase4_lines.append(f"### {s}")
        continue
    phase4_lines.append(s)

phase4_md.write_text('\n'.join(phase4_lines), encoding='utf-8')

# Phase 5: Post-processing
phase5_text = phase4_md.read_text(encoding='utf-8')

# clean TOC leader artifacts
phase5_lines: list[str] = []
for line in phase5_text.splitlines():
    phase5_lines.append(clean_toc_line(line))
phase5_text = '\n'.join(phase5_lines)

# replace TOC block with toc-extracted.txt content (preserve CRLFs)
lines = phase5_text.splitlines()
toc_lines = build_toc_block()
toc_line_set = set(toc_lines)
toc_title_norm = {normalize_heading_text(title) for _, title in load_toc()}
toc_titles = [title for _, title in load_toc()]
toc_plain_lines = {line.lstrip('- ').strip() for line in toc_lines}
contents_idx = None
for i, line in enumerate(lines):
    base = line.lstrip('#').strip()
    if 'contents' in normalize_heading_text(base):
        contents_idx = i
        break
if contents_idx is not None and toc_lines:
    new_lines = lines[: contents_idx + 1]
    new_lines.append('')
    new_lines.extend(toc_lines)
    # skip original TOC block until next heading-like line
    i = contents_idx + 1
    while i < len(lines):
        candidate = lines[i].strip()
        if is_mashed_toc_line(candidate, toc_titles):
            i += 1
            continue
        if candidate.startswith('#') or (candidate and is_all_caps(candidate) and len(candidate) <= 80):
            break
        i += 1
    # drop any mashed TOC line that may remain
    tail_lines: list[str] = []
    for tail in lines[i:]:
        stripped = tail.strip()
        if is_mashed_toc_line(stripped, toc_titles):
            continue
        if stripped in toc_plain_lines and not stripped.startswith(('- ', '#')):
            continue
        tail_lines.append(tail)
    new_lines.extend(tail_lines)
phase5_text = '\n'.join(new_lines)

# drop any remaining mashed TOC lines anywhere
filtered_lines: list[str] = []
for line in phase5_text.splitlines():
    stripped = line.strip()
    if is_mashed_toc_line(stripped, toc_titles):
        continue
    if len(re.findall(r'\d+', stripped)) >= 5 and len(stripped.split()) >= 15:
        continue
    if stripped in toc_plain_lines and not stripped.startswith(('- ', '#')):
        continue
    for title in toc_titles:
        if stripped.lower().startswith(title.lower()) and re.search(r'\d+$', stripped):
            if not stripped.startswith(('- ', '#')):
                stripped = ''
                break
    if stripped.isupper() and stripped and stripped[-1].isdigit():
        for title in toc_titles:
            if title.upper() in stripped:
                stripped = ''
                break
    if stripped == '' and line.strip() != '':
        continue
    filtered_lines.append(line)
phase5_text = '\n'.join(filtered_lines)

# fix hyphenation across line breaks
phase5_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', phase5_text)

# normalize line breaks within paragraphs
lines = phase5_text.splitlines()
merged: list[str] = []
for i, line in enumerate(lines):
    s = line.rstrip()
    if not s:
        merged.append('')
        continue
    if s.startswith('#') or s.startswith('- ') or s.startswith('>') or s in toc_line_set:
        merged.append(s)
        continue
    if i + 1 < len(lines) and lines[i + 1].strip() == '':
        merged.append(s)
        continue
    if merged and merged[-1] and not merged[-1].startswith(('#', '- ', '>')):
        merged[-1] = merged[-1] + ' ' + s
    else:
        merged.append(s)

phase5_text = '\n'.join(merged)

# fix excessive whitespace (preserve TOC indentation)
phase5_text = re.sub(r'\n{3,}', '\n\n', phase5_text)
normalized_lines: list[str] = []
for line in phase5_text.splitlines():
    if line.lstrip().startswith('-'):
        normalized_lines.append(line.rstrip())
        continue
    m = re.match(r'^(\s*)(.*)$', line)
    if m:
        indent, rest = m.groups()
        rest = re.sub(r'[ \t]{2,}', ' ', rest)
        normalized_lines.append(f"{indent}{rest}".rstrip())
    else:
        normalized_lines.append(line.rstrip())
phase5_text = '\n'.join(normalized_lines)

# final cleanup for any remaining mashed TOC residue
final_lines: list[str] = []
for line in phase5_text.splitlines():
    stripped = line.strip()
    # preserve numbered list items before TOC cleanup heuristics
    if re.match(r'^\d+\.', stripped) or re.search(r'\b\d+\.\s*[A-Za-z]', stripped):
        final_lines.append(line)
        continue
    if is_mashed_toc_line(stripped, toc_titles):
        continue
    if len(re.findall(r'\d+', stripped)) >= 5 and len(stripped.split()) >= 15:
        # keep numbered list items (e.g., 3. Skills: ...)
        # keep dice-notation paragraphs (e.g., 1D100, D6)
        if re.search(r'\b\d+D\d+\b|\bD\d+\b', stripped):
            final_lines.append(line)
            continue
        continue
    final_lines.append(line)
phase5_text = '\n'.join(final_lines)

# split merged numbered list items (e.g., "3.Skills ... 4.Weapons ...")
split_lines: list[str] = []
for line in phase5_text.splitlines():
    if re.search(r'\b\d+\.\s*[A-Za-z]', line):
        updated = re.sub(r'(?<!^)\s*(\d{1,2})\.\s*(?=[A-Za-z])', r'\n\1. ', line)
        for part in updated.splitlines():
            part = re.sub(r'^(\d+)\.(\S)', r'\1. \2', part)
            split_lines.append(part)
    else:
        split_lines.append(line)
phase5_text = '\n'.join(split_lines)

# drop any non-bullet lines inside the TOC block
toc_cleaned: list[str] = []
in_toc = False
for line in phase5_text.splitlines():
    stripped = line.strip()
    if stripped.startswith('#') and 'contents' in normalize_heading_text(stripped):
        in_toc = True
        toc_cleaned.append(line)
        continue
    if in_toc:
        if stripped.startswith('#') and 'contents' not in normalize_heading_text(stripped):
            in_toc = False
            toc_cleaned.append(line)
            continue
        if stripped == '' or stripped.lstrip().startswith('-'):
            toc_cleaned.append(line)
            continue
        # drop any stray non-bullet line inside TOC
        continue
    toc_cleaned.append(line)
phase5_text = '\n'.join(toc_cleaned)

# normalize quotes
phase5_text = phase5_text.replace('“', '"').replace('”', '"').replace('’', "'")

phase5_md.write_text(phase5_text, encoding='utf-8')

# Phase 6: Hierarchy correction using TOC
phase6_lines: list[str] = []

# build lookup from TOC
toc_items = load_toc()
toc_map = {normalize_heading_text(title): level for level, title in toc_items}
line_label_map = build_line_label_map(input_pdf)
heading_phrase_map = build_heading_phrase_map(input_pdf)
heading_phrases = sorted(heading_phrase_map.keys(), key=len, reverse=True)

in_toc = False
for line in phase5_md.read_text(encoding='utf-8').splitlines():
    stripped = line.strip()
    if not stripped:
        phase6_lines.append('')
        continue

    if stripped.startswith('#') and 'contents' in normalize_heading_text(stripped):
        in_toc = True
        phase6_lines.append(stripped)
        continue
    if in_toc and stripped.startswith('#') and 'contents' not in normalize_heading_text(stripped):
        in_toc = False

    if line.lstrip().startswith('- '):
        phase6_lines.append(line.rstrip())
        continue

    # remove existing heading markers for matching
    base = stripped.lstrip('#').strip()
    norm = normalize_heading_text(base)

    label = line_label_map.get(norm)
    if label:
        if label == '-':
            continue
        if label == 'body':
            if stripped.startswith('#'):
                phase6_lines.append(base)
                continue
        if label in {'#', '##', '###'}:
            phase6_lines.append(f"{label} {base}")
            continue
        if label == 'gm_note':
            phase6_lines.append(f"> **GM Note:** {base}")
            continue
        if label == 'quote':
            phase6_lines.append(f"> *{base}*")
            continue
        if label == 'quote_author':
            author = base.lstrip('—- ').strip()
            phase6_lines.append(f"> — {author}")
            continue

    if norm in toc_map:
        level = toc_map[norm]
        if level <= 1:
            prefix = '#'
        elif level == 2:
            prefix = '##'
        else:
            prefix = '###'
        phase6_lines.append(f"{prefix} {base}")
        continue
    if not in_toc and heading_phrases:
        matched = False
        for phrase_norm in heading_phrases:
            phrase_info = heading_phrase_map.get(phrase_norm)
            if not phrase_info:
                continue
            phrase_text = phrase_info['text']
            phrase_label = phrase_info['label']
            if phrase_norm not in normalize_heading_text(stripped):
                continue
            match = re.search(re.escape(phrase_text), stripped, flags=re.IGNORECASE)
            if not match:
                continue
            # only split when heading appears at a sentence boundary (avoid mid-sentence lowercase hits)
            before_idx = match.start() - 1
            while before_idx >= 0 and stripped[before_idx].isspace():
                before_idx -= 1
            if before_idx >= 0 and stripped[before_idx] not in '.!?':
                continue
            raw_match = match.group(0)
            if not any(c.isupper() for c in raw_match):
                continue
            split_pattern = re.compile(re.escape(raw_match), re.IGNORECASE)
            parts = split_pattern.split(stripped, maxsplit=1)
            if len(parts) != 2:
                continue
            before, after = parts
            if before.strip():
                phase6_lines.append(before.strip())
            phase6_lines.append(f"{phrase_label} {raw_match.strip()}")
            if after.strip():
                phase6_lines.append(after.strip())
            matched = True
            break
        if matched:
            continue

    phase6_lines.append(stripped)

# enforce no skipped headings (simple pass: ensure a top-level H1 exists)
if not any(l.startswith('# ') for l in phase6_lines):
    phase6_lines.insert(0, '# Call of Cthulhu Quick-Start Rules')
    phase6_lines.insert(1, '')

phase6_md.write_text('\n'.join(phase6_lines), encoding='utf-8')

print(f"Wrote {phase4_md}")
print(f"Wrote {phase5_md}")
print(f"Wrote {phase6_md}")
