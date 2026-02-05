# Research: PDF to Markdown Command Orchestration

**Date**: 2026-01-29
**Feature**: 005-pdf-convert-orchestration

## Overview

This document captures research findings for implementing the PDF conversion orchestration layer. The architecture is already well-defined in `specs/004-pdf-research/pdf-conversion-architecture.md` (v10), so research focuses on implementation patterns and best practices.

## Research Topics

### 1. CLI State Management Pattern

**Decision**: Use JSON file (`.state.json`) with atomic writes

**Rationale**:
- JSON is human-readable and debuggable (constitution: observability)
- Atomic writes prevent corruption on interruption
- Schema validation ensures integrity on resume
- Aligns with existing gmkit patterns (JSON configs)

**Alternatives Considered**:
- SQLite: Overkill for single-user CLI; adds dependency
- Pickle: Binary format violates observability principle
- YAML: Less tooling support than JSON

**Implementation Pattern**:
```python
import json
import tempfile
import os

def save_state(state_path: Path, state: dict) -> None:
    """Atomic write to prevent corruption on interruption."""
    temp_fd, temp_path = tempfile.mkstemp(dir=state_path.parent)
    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(state, f, indent=2)
        os.replace(temp_path, state_path)  # Atomic on POSIX
    except:
        os.unlink(temp_path)
        raise
```

### 2. PyMuPDF Metadata Extraction

**Decision**: Use `fitz.open()` with metadata property access

**Rationale**:
- PyMuPDF already a project dependency (from architecture research)
- Provides title, author, creator, producer, keywords, subject
- Can extract text sample for scanned PDF detection
- Cross-platform consistent behavior

**Alternatives Considered**:
- pypdf: Less feature-rich, inconsistent metadata handling
- pdfminer: Heavier dependency, focused on text extraction

**Implementation Pattern**:
```python
import fitz

def extract_metadata(pdf_path: Path) -> dict:
    """Extract PDF metadata for pre-flight report."""
    with fitz.open(pdf_path) as doc:
        meta = doc.metadata
        return {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "creator": meta.get("creator", ""),
            "producer": meta.get("producer", ""),
            "page_count": len(doc),
            "file_size_bytes": pdf_path.stat().st_size,
            "has_toc": len(doc.get_toc()) > 0,
            "image_count": sum(len(page.get_images()) for page in doc),
            "font_count": len(set(
                span["font"]
                for page in doc
                for block in page.get_text("dict")["blocks"]
                if block["type"] == 0
                for line in block["lines"]
                for span in line["spans"]
            )),
        }
```

### 3. Phase Interface for Mockability

**Decision**: Abstract base class with `execute()` method returning `PhaseResult`

**Rationale**:
- Clear contract for E4-07a/b/c/d implementers
- Easy to mock for unit/integration tests
- Supports step-level progress tracking
- Enables retry logic at orchestrator level

**Alternatives Considered**:
- Protocol classes: Less explicit, harder to document
- Function-based: Loses step-level tracking capability
- Event-based: Overly complex for sequential pipeline

**Implementation Pattern**:
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

class PhaseStatus(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"

@dataclass
class StepResult:
    step_id: str  # e.g., "0.1", "5.3"
    status: PhaseStatus
    message: str
    output_file: Optional[Path] = None

@dataclass
class PhaseResult:
    phase_num: int
    status: PhaseStatus
    steps: List[StepResult]
    warnings: List[str]
    errors: List[str]

class Phase(ABC):
    """Base class for all pipeline phases."""

    @property
    @abstractmethod
    def phase_num(self) -> int:
        """Phase number (0-10)."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable phase name."""
        pass

    @abstractmethod
    def execute(self, context: "ConversionContext") -> PhaseResult:
        """Execute this phase. Returns result with step-level details."""
        pass

    def can_resume_from(self, step_id: str) -> bool:
        """Check if phase supports resuming from a specific step."""
        return True  # Default: phases support step-level resume
```

### 4. Pre-flight Analysis Implementation

**Decision**: Separate preflight module with individual analysis functions

**Rationale**:
- Each step (0.1-0.5) is independently testable
- Enables parallel execution if needed later
- Clear mapping to spec requirements (FR-011 through FR-016)

**Implementation Pattern**:
```python
# preflight.py
def analyze_pdf(pdf_path: Path) -> PreflightReport:
    """Run all pre-flight checks and return consolidated report."""
    return PreflightReport(
        file_metrics=extract_file_metrics(pdf_path),      # Step 0.1
        image_count=count_images(pdf_path),                # Step 0.2
        toc_info=detect_toc(pdf_path),                     # Step 0.3
        text_extractability=check_text(pdf_path),          # Step 0.4
        font_analysis=analyze_fonts(pdf_path),             # Step 0.5
        complexity=estimate_complexity(...),               # Derived
        user_involvement=determine_user_phases(...),       # Derived
    )
```

### 5. Slash Command Prompt Design

**Decision**: Minimal prompt that invokes CLI with argument passthrough

**Rationale**:
- Keeps logic in CLI (testable, maintainable)
- Agent-agnostic - works with all supported agents
- Prompt file is documentation as much as instruction

**Template Pattern**:
```markdown
# /gmkit.pdf-to-markdown

Convert a PDF file to Markdown format using the GM-Kit conversion pipeline.

## Usage

/gmkit.pdf-to-markdown "<pdf-path>"

## What This Does

1. Runs pre-flight analysis on the PDF
2. Shows complexity report and user involvement notice
3. Asks for confirmation before proceeding
4. Executes the 11-phase conversion pipeline
5. Produces final Markdown in the output directory

## CLI Equivalent

This command invokes:
```bash
gmkit pdf-convert "<pdf-path>" --output ./converted/
```

## Arguments

- `<pdf-path>`: Path to the PDF file to convert (required)

## Options

Add these after the PDF path:
- `--output <dir>`: Custom output directory (default: ./converted/)
- `--diagnostics`: Include diagnostic bundle in output
```

### 6. Testing Strategy

**Decision**: Three-tier testing with mocks at integration boundary

**Rationale**:
- Unit tests: Fast, isolated, use mocks for all external dependencies
- Integration tests: Use pexpect for CLI interaction, mocks for phases
- Contract tests: Validate phase interface contracts for E4-07a/b/c/d

**Test Doubles**:
```python
# tests/conftest.py
@pytest.fixture
def mock_phases():
    """Provide mock implementations for all phases."""
    return {
        1: MockPhase(phase_num=1, name="Image Extraction"),
        2: MockPhase(phase_num=2, name="Image Removal"),
        # ... etc
    }

@pytest.fixture
def mock_user_interaction():
    """Mock E4-07c user interaction (step 0.6)."""
    return MockUserInteraction(auto_confirm=True)
```

## Summary

All research topics resolved with clear implementation patterns. No blockers identified. Ready to proceed to Phase 1 design artifacts.

### Key Decisions

| Topic | Decision | Key Benefit |
|-------|----------|-------------|
| State Management | JSON with atomic writes | Debuggable, corruption-resistant |
| Metadata Extraction | PyMuPDF | Already a dependency, comprehensive |
| Phase Interface | ABC with PhaseResult | Mockable, step-level tracking |
| Pre-flight | Separate analysis functions | Independently testable |
| Prompt Design | Minimal, CLI passthrough | Agent-agnostic, testable |
| Testing | Three-tier with mocks | Fast units, realistic integration |
