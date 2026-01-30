from pathlib import Path
import fitz

root = Path('/home/todd/Dev/gm-kit')
input_pdf = root / 'temp-resources/CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf'
output_pdf = root / 'temp-resources/conversions/call-of-cthulhu/codex/preprocessed/call-of-cthulhu-no-images-delete.pdf'

with fitz.open(input_pdf) as doc:
    for page in doc:
        image_list = page.get_images(full=True)
        for img in image_list:
            xref = img[0]
            page.delete_image(xref)
    doc.save(output_pdf, garbage=4, deflate=True)

print(f"Images removed. Output saved to: {output_pdf}")
