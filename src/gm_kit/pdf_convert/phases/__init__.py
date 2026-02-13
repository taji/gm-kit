"""Phase execution module for PDF conversion pipeline.

Contains the Phase interface and implementations for each pipeline phase.
"""

from gm_kit.pdf_convert.phases.base import (
                                            Phase,
                                            PhaseRegistry,
                                            PhaseResult,
                                            PhaseStatus,
                                            StepResult,
                                            get_phase_registry,
)

# Import all phase classes for convenient access
from gm_kit.pdf_convert.phases.phase0 import Phase0
from gm_kit.pdf_convert.phases.phase1 import Phase1
from gm_kit.pdf_convert.phases.phase2 import Phase2
from gm_kit.pdf_convert.phases.phase3 import Phase3
from gm_kit.pdf_convert.phases.phase4 import Phase4
from gm_kit.pdf_convert.phases.phase5 import Phase5
from gm_kit.pdf_convert.phases.phase6 import Phase6
from gm_kit.pdf_convert.phases.phase7 import Phase7
from gm_kit.pdf_convert.phases.phase8 import Phase8
from gm_kit.pdf_convert.phases.phase9 import Phase9
from gm_kit.pdf_convert.phases.phase10 import Phase10

__all__ = [
    "Phase",
    "PhaseRegistry",
    "PhaseResult",
    "PhaseStatus",
    "StepResult",
    "get_phase_registry",
    # Phase classes
    "Phase0",
    "Phase1",
    "Phase2",
    "Phase3",
    "Phase4",
    "Phase5",
    "Phase6",
    "Phase7",
    "Phase8",
    "Phase9",
    "Phase10",
]
