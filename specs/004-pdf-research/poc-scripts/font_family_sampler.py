from __future__ import annotations
from pathlib import Path
from collections import defaultdict, Counter
import json
import re
import fitz

root = Path('/home/todd/Dev/gm-kit')
work_dir = root / 'temp-resources/conversions/call-of-cthulhu/codex'
input_pdf = work_dir / 'preprocessed' / 'call-of-cthulhu-no-images-delete.pdf'
toc_path = work_dir / 'toc-extracted.txt'
mapping_path = work_dir / 'font-family-mapping.json'

samples_per_family = 8


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_all_caps(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    return all(c.isupper() for c in letters)


toc_titles: dict[str, int] = {}
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
            toc_titles[normalize(title)] = level


def label_for_text(text: str) -> str:
    norm = normalize(text)
    if norm in toc_titles:
        level = toc_titles[norm]
        if level <= 1:
            return '#'
        if level == 2:
            return '##'
        return '###'
    return ''


# group key: (rounded_size, font_name)
family_samples: dict[tuple[float, str], list[dict]] = defaultdict(list)
family_labels: dict[tuple[float, str], str] = {}
family_overrides: dict[tuple[float, str], list[dict]] = defaultdict(list)
family_texts: dict[tuple[float, str], list[str]] = defaultdict(list)

if mapping_path.exists():
    try:
        existing = json.loads(mapping_path.read_text(encoding='utf-8'))
        families = existing.get('families', []) if isinstance(existing, dict) else []
        for item in families:
            size = float(item.get('size', 0.0))
            font = str(item.get('font', '')).strip()
            if not font:
                continue
            key = (size, font)
            label = str(item.get('label', '')).strip()
            if label:
                family_labels[key] = label
            overrides = item.get('overrides', [])
            if isinstance(overrides, list) and overrides:
                family_overrides[key] = overrides
    except json.JSONDecodeError:
        pass

with fitz.open(input_pdf) as doc:
    for page_index, page in enumerate(doc):
        data = page.get_text('dict')
        for block in data.get('blocks', []):
            for line in block.get('lines', []):
                line_text = ''.join(span.get('text', '') for span in line.get('spans', [])).strip()
                if not line_text:
                    continue
                if len(line_text) < 3 or line_text.isdigit():
                    continue
                spans = line.get('spans', [])
                if not spans:
                    continue
                dominant = max(spans, key=lambda s: len(s.get('text', '')))
                size = float(dominant.get('size', 0))
                font = dominant.get('font', 'unknown')
                rounded_size = round(size, 1)
                key = (rounded_size, font)

                family_texts[key].append(line_text)

                if len(family_samples[key]) < samples_per_family:
                    family_samples[key].append({
                        'page': page_index + 1,
                        'text': line_text
                    })

                if key not in family_labels or family_labels[key] == '':
                    guess = label_for_text(line_text)
                    if guess:
                        family_labels[key] = guess

# sort families by size desc then font
families = sorted(family_samples.items(), key=lambda kv: (-kv[0][0], kv[0][1]))

mapping = {
    'notes': (
        'Prefilled labels are best guesses based on matching TOC titles. '\
        'Use "#", "##", "###" for headings. '\
        'Use custom tags like "body", "read_aloud", "gm_note" for later formatting. '\
        'Note: "-" is ignored and treated as body.'
    ),
    'families': [
        {
            'size': size,
            'font': font,
            'label': family_labels.get((size, font), ''),
            'overrides': family_overrides.get((size, font), []),
            'samples': samples
        }
        for (size, font), samples in families
    ]
}

mapping_path.write_text(json.dumps(mapping, indent=2), encoding='utf-8')

print('Wrote', mapping_path)
