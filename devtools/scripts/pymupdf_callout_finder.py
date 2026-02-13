import fitz  # PyMuPDF
from pathlib import Path

def find_callout_text_in_pdf(pdf_path: Path, start_text: str, end_text: str):
    """
    Finds and prints text content within a specified boundary in a PDF.
    """
    doc = fitz.open(pdf_path)
    in_callout_block = False
    callout_text = []

    print(f"Searching for callout in '{pdf_path.name}'...")
    print(f"Start marker: '{start_text}'")
    print(f"End marker:   '{end_text}'")
    print("-" * 20)

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("blocks")
        for block in blocks:
            block_text = block[4] # The text content of the block

            if start_text in block_text:
                in_callout_block = True
                # If start and end are in the same block
                if end_text in block_text:
                    start_index = block_text.find(start_text)
                    end_index = block_text.find(end_text) + len(end_text)
                    callout_text.append(block_text[start_index:end_index])
                    in_callout_block = False # Reset for next potential callout
                else:
                    callout_text.append(block_text[block_text.find(start_text):])

            elif end_text in block_text and in_callout_block:
                callout_text.append(block_text[:block_text.find(end_text) + len(end_text)])
                in_callout_block = False

            elif in_callout_block:
                callout_text.append(block_text)

    if callout_text:
        print("Callout text found:")
        print("".join(callout_text).strip())
    else:
        print("Callout text not found.")

if __name__ == "__main__":
    pdf_file = Path("tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf")
    start_marker = "PDF Creation"
    end_marker = "snippet to your brew!"

    if pdf_file.exists():
        find_callout_text_in_pdf(pdf_file, start_marker, end_marker)
    else:
        print(f"Error: PDF file not found at '{pdf_file}'")
