"""Phase 2: Image Removal.

Code steps 2.1-2.2: Create no-images PDF by removing images.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult
from gm_kit.pdf_convert.prep.handlers import create_no_images_pdf

if TYPE_CHECKING:
    from gm_kit.pdf_convert.state import ConversionState

logger = logging.getLogger(__name__)


class Phase2(Phase):
    """Phase 2: Image Removal.

    Creates a no-images PDF by replacing images with empty rectangles,
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
            images_removed = create_no_images_pdf(
                pdf_path=pdf_path,
                output_pdf_path=output_pdf_path,
            )

            result.add_step(
                StepResult(
                    step_id="2.1",
                    description="Identify image bounding boxes",
                    status=PhaseStatus.SUCCESS,
                    message=f"Found and covered {images_removed} image instances",
                )
            )

            result.add_step(
                StepResult(
                    step_id="2.2",
                    description="Create no-images PDF",
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
