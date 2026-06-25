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
from gm_kit.pdf_convert.prep.handlers import extract_images_to_artifacts

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

        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            manifest_path, total_images = extract_images_to_artifacts(
                pdf_path=pdf_path,
                images_dir=images_dir,
            )
            with open(manifest_path, encoding="utf-8") as manifest_file:
                manifest = json.load(manifest_file)
            image_manifest = manifest["images"]

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
