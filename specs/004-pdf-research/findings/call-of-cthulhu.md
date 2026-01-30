# Call of Cthulhu Starter Set Findings

## Metadata
- PDF title: Call of Cthulhu Starter Set (7th Edition)
- Source file: `temp-resources/chunks/call-of-cthulhu/coc-11-20.pdf`
- Chunk(s) tested: 11–20 (10 pages)
- Conversion approach: AI-only (Claude Code native PDF read)
- Agent/tool: Claude Code (Opus 4.5)
- Commands used:
  - Direct PDF read (failed due to size)
  - `gs -o <output> -sDEVICE=pdfwrite -dFILTERIMAGE <input>` (ghostscript image strip)
  - PDF read on image-stripped file (succeeded)
- Output location: `temp-resources/chunks/call-of-cthulhu/coc-11-20-no-images.pdf`
- Date: 2026-01-26

## Checklist Summary
- Checklist file: `specs/004-pdf-research/findings/review-checklist.md`
- Overall pass/fail: Pass (with ghostscript preprocessing)

## Results
- Structural accuracy: Good; headings, sections, and page flow preserved
- Callouts & special blocks: Boxed text (Levels of Success, Weapon Damage, Other Forms of Damage table, About Ready-Made Investigators) extracted correctly
- Text quality & cleanup: Clean text extraction; no OCR artifacts
- Tables: Other Forms of Damage table preserved with columns (Injury, Damage, Examples)
- OCR quality: N/A (native text PDF)
- Image handling: Images stripped via ghostscript; blank spaces remain where artwork was

## Issues & Fixes
- Issue: "Request too large" error when reading coc-11-20.pdf directly
  - Impact: Unable to process 10-page chunks of visually-dense RPG PDFs
  - Fix/workaround: Use ghostscript to strip images before reading: `gs -o <output> -sDEVICE=pdfwrite -dFILTERIMAGE <input>`
  - Notes: File size reduced from 2.1MB to 142KB (93% reduction). All text content preserved.

- Issue: 10-page chunks exceed Claude Code's request size limit for image-heavy PDFs
  - Impact: Larger chunks fail; smaller chunks (1-5 pages) may succeed
  - Fix/workaround: Either reduce chunk size to ~5 pages or fewer, or preprocess with ghostscript to strip images
  - Notes: Other chunks in the folder (`coc-21-30`, `coc-31-40`) are also 10 pages and would likely fail without preprocessing

## Observations
- What worked well: Ghostscript image stripping is fast and effective; text extraction quality was excellent after preprocessing
- What broke: Direct multimodal PDF read on 10-page image-heavy chunks
- Surprises: The 93% file size reduction demonstrates how much of RPG PDF size is artwork vs text content

## Content Summary (Pages 10-19)
- **Page 10**: Game system overview, skill rolls, difficulty levels (Regular/Hard/Extreme), pushing rolls
- **Page 11**: Bonus and penalty dice mechanics with detailed examples (Malcolm/Hugh, Felix/Harrison)
- **Page 12**: Luck rolls, Sanity (SAN) mechanics, temporary insanity, bouts of madness, delusions
- **Page 13**: Combat basics, DEX order, close combat, fighting back vs dodging, extreme damage
- **Page 14**: Fighting maneuvers, outnumbered rules, firearms, hit points/wounds/healing
- **Page 15**: Other Forms of Damage table, ready-made investigators introduction
- **Page 16**: (Full-page illustration - blank after image strip)
- **Pages 17-19**: "The Haunting" scenario begins - Location 1 (Introduction/Mr. Knott), Location 2 (Boston Globe), Location 3 (Central Library)

## Chunking Recommendations for Call of Cthulhu
Based on the chunk files in `temp-resources/chunks/call-of-cthulhu/`:

| Chunk | Pages | Likely to succeed directly? |
|-------|-------|----------------------------|
| coc-01-04.pdf | 4 | Yes |
| coc-05-05.pdf | 1 | Yes |
| coc-06-10.pdf | 5 | Yes |
| coc-11-20.pdf | 10 | No (needs preprocessing) |
| coc-21-30.pdf | 10 | No (needs preprocessing) |
| coc-31-40.pdf | 10 | No (needs preprocessing) |
| coc-41-45.pdf | 5 | Likely yes |
| coc-46-48.pdf | 3 | Yes |
| coc-49-50.pdf | 2 | Yes |

## Next Steps
- Process remaining 10-page chunks with ghostscript preprocessing
- Compare Claude extraction against Gemini/Qwen for this PDF
- Test if 5-page chunks of visually-dense content succeed without preprocessing
- Consider adding ghostscript preprocessing to standard workflow for large chunks
