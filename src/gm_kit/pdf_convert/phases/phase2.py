"""Phase 2: Image Removal.

Code steps 2.1-2.2: Create text-only PDF by removing images.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import fitz  # PyMuPDF

from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState

logger = logging.getLogger(__name__)


class Phase2(Phase):
    """Phase 2: Image Removal.

    Creates a text-only PDF by replacing images with empty rectangles,
    preserving layout for text extraction.
    """

    @property
    def phase_num(self) -> int:
        return 2

    def execute(self, state: ConversionState) -> PhaseResult:
        """Execute image removal steps.

        Args:
            state: Current conversion state

        Returns:
            PhaseResult with removal results
        """
        result = self.create_result()
        pdf_path = Path(state.pdf_path)
        output_dir = Path(state.output_dir)
        preprocessed_dir = output_dir / "preprocessed"
        preprocessed_dir.mkdir(exist_ok=True)

        pdf_name = pdf_path.stem
        output_pdf_path = preprocessed_dir / f"{pdf_name}-no-images.pdf"

        try:
            # Step 2.1: Identify image bounding boxes
            doc = fitz.open(pdf_path)
            images_removed = 0

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()

                for img in image_list:
                    xref = img[0]
                    # Get all rectangles for this image
                    rects = page.get_image_rects(xref)
                    for rect in rects:
                        # Cover image with white rectangle
                        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                        images_removed += 1

            result.add_step(
                StepResult(
                    step_id="2.1",
                    description="Identify image bounding boxes",
                    status=PhaseStatus.SUCCESS,
                    message=f"Found and covered {images_removed} image instances",
                )
            )

            # Step 2.2: Create text-only PDF
            doc.save(output_pdf_path)
            doc.close()

            result.add_step(
                StepResult(
                    step_id="2.2",
                    description="Create text-only PDF",
                    status=PhaseStatus.SUCCESS,
                    message=f"Saved to {output_pdf_path}",
                )
            )
            result.output_file = str(output_pdf_path)

        except Exception as e:
            result.add_step(
                StepResult(
                    step_id="2.1",
                    description="Identify image bounding boxes",
                    status=PhaseStatus.ERROR,
                    message=str(e),
                )
            )
            result.add_error(f"Image removal failed: {e}")

        result.complete()
        return result
