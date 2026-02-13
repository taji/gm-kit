"""Phase 1: Image Extraction.

Code steps 1.1-1.4: Extract images from PDF and create image manifest.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import fitz  # PyMuPDF

from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState

logger = logging.getLogger(__name__)


class Phase1(Phase):
    """Phase 1: Image Extraction.

    Extracts images from PDF pages and creates an image manifest
    with position data for later link injection.
    """

    @property
    def phase_num(self) -> int:
        return 1

    def execute(self, state: ConversionState) -> PhaseResult:
        """Execute image extraction steps.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with extraction results
        """
        result = self.create_result()
        pdf_path = Path(state.pdf_path)
        output_dir = Path(state.output_dir)
        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)

        # Step 1.1: Identify images per page
        image_manifest = []
        total_images = 0

        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)

            for page_num in range(page_count):
                page = doc[page_num]
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]

                    # Generate filename
                    img_filename = f"page{page_num + 1:03d}_img{img_index + 1:02d}.png"
                    img_path = images_dir / img_filename

                    # Save image bytes
                    img_path.write_bytes(image_bytes)

                    # Get image position on page
                    rect = page.get_image_rects(xref)
                    if rect:
                        rect = rect[0]
                        position = {
                            "x": rect.x0,
                            "y": rect.y0,
                            "width": rect.width,
                            "height": rect.height,
                        }
                    else:
                        position = {"x": 0, "y": 0, "width": 0, "height": 0}

                    # Add to manifest
                    image_manifest.append(
                        {
                            "page": page_num + 1,
                            "filename": img_filename,
                            "position": position,
                        }
                    )

                    total_images += 1

            doc.close()

            result.add_step(
                StepResult(
                    step_id="1.1",
                    description="Identify images per page",
                    status=PhaseStatus.SUCCESS,
                    message=f"Found {total_images} images across {page_count} pages",
                )
            )

        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="1.1",
                    description="Identify images per page",
                    status=PhaseStatus.ERROR,
                    message=str(e),
                )
            )
            result.add_error(f"Image identification failed: {e}")
            result.complete()
            return result

        # Step 1.2: Extract images to files
        # Already done in step 1.1
        result.add_step(
            StepResult(
                step_id="1.2",
                description="Extract images to files",
                status=PhaseStatus.SUCCESS,
                message=f"Extracted {total_images} images to {images_dir}",
            )
        )

        # Step 1.3: Generate alt-text placeholders
        # For now, generate simple placeholders based on position
        for img in image_manifest:
            img["alt_text"] = f"[Figure on page {img['page']}"

        result.add_step(
            StepResult(
                step_id="1.3",
                description="Generate alt-text placeholders",
                status=PhaseStatus.SUCCESS,
                message=f"Generated placeholders for {len(image_manifest)} images",
            )
        )

        # Step 1.4: Create image-manifest.json
        try:
            manifest_path = images_dir / "image-manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "images": image_manifest,
                        "total_count": len(image_manifest),
                    },
                    f,
                    indent=2,
                    sort_keys=True,
                )

            result.add_step(
                StepResult(
                    step_id="1.4",
                    description="Create image-manifest.json",
                    status=PhaseStatus.SUCCESS,
                    message=f"Manifest saved to {manifest_path}",
                )
            )
            result.output_file = str(manifest_path)

        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="1.4",
                    description="Create image-manifest.json",
                    status=PhaseStatus.ERROR,
                    message=str(e),
                )
            )
            result.add_error(f"Failed to create image manifest: {e}")

        result.complete()
        return result
