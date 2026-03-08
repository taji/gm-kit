"""Table step helpers for on-demand page rendering and image path generation.

This module provides utilities for:
1. On-demand page image rendering using PyMuPDF
2. Bounding box to pixel coordinate conversion
3. Table crop image generation
4. Input payload building for multimodal table steps (7.7, 8.7)
"""

import os
from pathlib import Path

try:
    import fitz  # PyMuPDF

    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def render_page_image(
    pdf_path: str, page_num: int, output_path: str, dpi: int | None = None
) -> str:
    """Render a single page from PDF to PNG image.

    Args:
        pdf_path: Path to source PDF
        page_num: 0-based page number
        output_path: Path for output PNG file
        dpi: Resolution (default: GM_PAGE_IMAGE_DPI env var or 150)

    Returns:
        Path to rendered image

    Raises:
        RuntimeError: If PyMuPDF not available
        FileNotFoundError: If PDF not found
    """
    if not HAS_PYMUPDF:
        raise RuntimeError("PyMuPDF required for page rendering")

    if dpi is None:
        dpi = int(os.environ.get("GM_PAGE_IMAGE_DPI", 150))

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_file))
    try:
        page = doc.load_page(page_num)
        # Convert DPI to zoom factor (72 DPI is base)
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=mat)
        pixmap.save(str(output_file))
    finally:
        doc.close()

    return str(output_file)


def crop_table_image(page_image_path: str, bbox_pixels: dict[str, int], output_path: str) -> str:
    """Crop table region from page image.

    Args:
        page_image_path: Path to full page image
        bbox_pixels: Bounding box {x0, y0, x1, y1} in pixels
        output_path: Path for cropped output

    Returns:
        Path to cropped image

    Raises:
        RuntimeError: If Pillow not available
    """
    if not HAS_PILLOW:
        raise RuntimeError("Pillow required for image cropping")

    page_img = Image.open(page_image_path)

    # Crop using bounding box coordinates
    crop_box = (bbox_pixels["x0"], bbox_pixels["y0"], bbox_pixels["x1"], bbox_pixels["y1"])

    cropped = page_img.crop(crop_box)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(str(output_file))

    return str(output_file)


def bbox_points_to_pixels(
    bbox_points: dict[str, float],
    page_width_pts: float,
    page_height_pts: float,
    image_width_px: int,
    image_height_px: int,
) -> dict[str, int]:
    """Convert PDF points coordinates to pixel coordinates.

    PDF uses points (72 per inch), images use pixels.
    PyMuPDF renders at specified DPI, so we need to scale.

    Args:
        bbox_points: Bounding box in PDF points {x0, y0, x1, y1}
        page_width_pts: Page width in points
        page_height_pts: Page height in points
        image_width_px: Rendered image width in pixels
        image_height_px: Rendered image height in pixels

    Returns:
        Bounding box in pixels
    """
    scale_x = image_width_px / page_width_pts
    scale_y = image_height_px / page_height_pts

    return {
        "x0": int(bbox_points["x0"] * scale_x),
        "y0": int(bbox_points["y0"] * scale_y),
        "x1": int(bbox_points["x1"] * scale_x),
        "y1": int(bbox_points["y1"] * scale_y),
    }


def build_step_7_7_input_payload(
    pdf_path: str, page_num: int, extracted_text: str, workspace: str, dpi: int | None = None
) -> dict:
    """Build input payload for step 7.7 (table detection).

    This is the first pass - text scan only. If tables detected,
    the system renders the page image for pass 2.

    Args:
        pdf_path: Path to source PDF
        page_num: 0-based page number
        extracted_text: Text extracted from the page
        workspace: Conversion workspace directory
        dpi: Resolution for rendering (if needed)

    Returns:
        Input payload dictionary for step-input.json
    """
    if dpi is None:
        dpi = int(os.environ.get("GM_PAGE_IMAGE_DPI", 150))

    # Calculate image path (relative to project root for fixtures)
    page_images_dir = Path(workspace) / "page_images"
    page_image_path = page_images_dir / f"page_{page_num + 1:03d}.png"

    return {
        "step_id": "7.7",
        "source_pdf": pdf_path,
        "page_number_1based": page_num + 1,
        "extracted_text": extracted_text,
        "dpi": dpi,
        "page_image": str(page_image_path),
        "phase": "text_scan",  # First pass
    }


def build_step_7_7_vision_payload(
    pdf_path: str,
    page_num: int,
    detected_tables: list[dict],
    workspace: str,
    dpi: int | None = None,
) -> list[dict]:
    """Build input payloads for step 7.7 vision pass.

    After text scan detects tables, render page image and
    create payloads for vision-based bounding box extraction.

    Args:
        pdf_path: Path to source PDF
        page_num: 0-based page number
        detected_tables: Tables detected from text scan
        workspace: Conversion workspace directory
        dpi: Resolution for rendering

    Returns:
        List of input payloads (one per detected table)
    """
    if dpi is None:
        dpi = int(os.environ.get("GM_PAGE_IMAGE_DPI", 150))

    # Ensure page image is rendered
    page_images_dir = Path(workspace) / "page_images"
    page_images_dir.mkdir(parents=True, exist_ok=True)
    page_image_path = page_images_dir / f"page_{page_num + 1:03d}.png"

    if not page_image_path.exists():
        render_page_image(pdf_path, page_num, str(page_image_path), dpi)

    payloads = []
    for table in detected_tables:
        payload = {
            "step_id": "7.7",
            "source_pdf": pdf_path,
            "page_number_1based": page_num + 1,
            "page_image": str(page_image_path),
            "table_id": table["table_id"],
            "text_context": table.get("text_context", ""),
            "phase": "vision_confirmation",
        }
        payloads.append(payload)

    return payloads


def build_step_8_7_input_payload(
    table_data: dict,
    page_image_path: str,
    flat_text_path: str,
    workspace: str,
    dpi: int | None = None,
) -> dict:
    """Build input payload for step 8.7 (table conversion).

    Args:
        table_data: Table info from step 7.7 (table_id, bbox_pixels, etc.)
        page_image_path: Path to full page image
        flat_text_path: Path to garbled flat text from table area
        workspace: Conversion workspace directory
        dpi: Resolution for cropping

    Returns:
        Input payload dictionary
    """
    if dpi is None:
        dpi = int(os.environ.get("GM_PAGE_IMAGE_DPI", 150))

    table_id = table_data["table_id"]

    # Crop table image if it doesn't exist
    table_crops_dir = Path(workspace) / "table_crops"
    table_crops_dir.mkdir(parents=True, exist_ok=True)
    crop_path = table_crops_dir / f"{table_id}_crop.png"

    if not crop_path.exists():
        crop_table_image(page_image_path, table_data["bbox_pixels"], str(crop_path))

    return {
        "step_id": "8.7",
        "table_id": table_id,
        "page_number_1based": table_data["page_number_1based"],
        "dpi": dpi,
        "page_image": page_image_path,
        "table_crop_image": str(crop_path),
        "bbox_pixels": table_data["bbox_pixels"],
        "flat_text_file": flat_text_path,
        "table_slug": table_data.get("table_slug", table_id),
    }


def get_page_dimensions(pdf_path: str, page_num: int) -> tuple[float, float]:
    """Get page dimensions in points.

    Args:
        pdf_path: Path to PDF
        page_num: 0-based page number

    Returns:
        (width, height) in points
    """
    if not HAS_PYMUPDF:
        raise RuntimeError("PyMuPDF required")

    doc = fitz.open(str(pdf_path))
    try:
        page = doc.load_page(page_num)
        rect = page.rect
        return rect.width, rect.height
    finally:
        doc.close()
