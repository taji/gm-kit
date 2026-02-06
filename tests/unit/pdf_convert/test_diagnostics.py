"""Unit tests for diagnostic bundle creation (T030)."""

import zipfile

from gm_kit.pdf_convert.orchestrator import create_diagnostic_bundle, sanitize_filename
from gm_kit.pdf_convert.state import ConversionState


class TestSanitizeFilename:
    """Tests for sanitize_filename helper."""

    def test_sanitize_filename__should_pass_through__when_normal_filename(self):
        """Normal filename passes through unchanged."""
        assert sanitize_filename("my-document.pdf") == "my-document.pdf"

    def test_sanitize_filename__should_replace_chars__when_windows_invalid_chars(self):
        """Replaces Windows-invalid characters with underscores."""
        assert sanitize_filename("file<name>test") == "file_name_test"
        assert sanitize_filename('file:name"test') == "file_name_test"
        assert sanitize_filename("file|name?test*") == "file_name_test_"

    def test_sanitize_filename__should_preserve_spaces__when_spaces_present(self):
        """Spaces are preserved."""
        assert sanitize_filename("my document.pdf") == "my document.pdf"


class TestDiagnosticBundleCreation:
    """Tests for create_diagnostic_bundle function."""

    def test_diagnostic_bundle__should_return_none__when_diagnostics_disabled(self, tmp_path):
        """Returns None when diagnostics_enabled is False."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=False,
        )

        result = create_diagnostic_bundle(state)
        assert result is None

    def test_diagnostic_bundle__should_create_zip_file__when_diagnostics_enabled(self, tmp_path):
        """Creates a zip file when diagnostics enabled."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        # Create some files that would be included
        (tmp_path / ".state.json").write_text("{}")
        (tmp_path / "metadata.json").write_text('{"page_count": 1}')

        result = create_diagnostic_bundle(state)

        assert result is not None
        assert result.exists()
        assert result.name == "diagnostic-bundle.zip"

    def test_diagnostic_bundle__should_be_valid_zip__when_created(self, tmp_path):
        """Created bundle is a valid zip file."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        (tmp_path / ".state.json").write_text("{}")

        result = create_diagnostic_bundle(state)

        assert result is not None
        assert zipfile.is_zipfile(result)

    def test_diagnostic_bundle__should_include_state_file__when_state_present(self, tmp_path):
        """Bundle includes .state.json when present."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        state_content = '{"version": "1.0"}'
        (tmp_path / ".state.json").write_text(state_content)

        result = create_diagnostic_bundle(state)

        assert result is not None
        with zipfile.ZipFile(result, 'r') as zf:
            assert ".state.json" in zf.namelist()
            assert zf.read(".state.json").decode() == state_content

    def test_diagnostic_bundle__should_include_metadata_file__when_metadata_present(self, tmp_path):
        """Bundle includes metadata.json when present."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        metadata_content = '{"page_count": 100}'
        (tmp_path / "metadata.json").write_text(metadata_content)

        result = create_diagnostic_bundle(state)

        assert result is not None
        with zipfile.ZipFile(result, 'r') as zf:
            assert "metadata.json" in zf.namelist()
            assert zf.read("metadata.json").decode() == metadata_content

    def test_diagnostic_bundle__should_include_cli_args__when_cli_args_configured(self, tmp_path):
        """Bundle includes cli-args.txt with CLI arguments."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
            config={"cli_args": "pdf-convert test.pdf --diagnostics"},
        )

        result = create_diagnostic_bundle(state)

        assert result is not None
        with zipfile.ZipFile(result, 'r') as zf:
            assert "cli-args.txt" in zf.namelist()
            assert "pdf-convert test.pdf --diagnostics" in zf.read("cli-args.txt").decode()

    def test_diagnostic_bundle__should_skip_missing_files__when_optional_files_absent(self, tmp_path):
        """Bundle gracefully handles missing optional files."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        # Only create state file, not metadata
        (tmp_path / ".state.json").write_text("{}")

        result = create_diagnostic_bundle(state)

        assert result is not None
        with zipfile.ZipFile(result, 'r') as zf:
            assert ".state.json" in zf.namelist()
            # metadata.json should not be in bundle
            assert "metadata.json" not in zf.namelist()

    def test_diagnostic_bundle__should_include_phase_outputs__when_phase_files_present(self, tmp_path):
        """Bundle includes phase output files when present."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        # Create phase output files
        (tmp_path / "test-phase4.md").write_text("Phase 4 output")
        (tmp_path / "test-phase5.md").write_text("Phase 5 output")

        result = create_diagnostic_bundle(state)

        assert result is not None
        with zipfile.ZipFile(result, 'r') as zf:
            names = zf.namelist()
            assert "test-phase4.md" in names
            assert "test-phase5.md" in names

    def test_diagnostic_bundle__should_include_conversion_report__when_report_present(self, tmp_path):
        """Bundle includes conversion-report.md when present."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        (tmp_path / "conversion-report.md").write_text("# Conversion Report")

        result = create_diagnostic_bundle(state)

        assert result is not None
        with zipfile.ZipFile(result, 'r') as zf:
            assert "conversion-report.md" in zf.namelist()


class TestBundleNaming:
    """Tests for diagnostic bundle naming per FR-010c."""

    def test_diagnostic_bundle__should_be_named_diagnostic_bundle_zip__when_created(self, tmp_path):
        """Bundle is named diagnostic-bundle.zip."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        result = create_diagnostic_bundle(state)

        assert result.name == "diagnostic-bundle.zip"

    def test_diagnostic_bundle__should_create_in_output_dir__when_created(self, tmp_path):
        """Bundle is created in the output directory."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        result = create_diagnostic_bundle(state)

        assert result.parent == tmp_path


class TestBundleErrorHandling:
    """Tests for error handling during bundle creation."""

    def test_diagnostic_bundle__should_return_none__when_permission_error(self, tmp_path, monkeypatch):
        """Returns None if bundle creation fails."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        # Make the output dir read-only to cause write failure
        def mock_zipfile_init(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(zipfile, "ZipFile", mock_zipfile_init)

        result = create_diagnostic_bundle(state)

        # Should return None, not raise
        assert result is None

    def test_diagnostic_bundle__should_use_deflated_compression__when_created(self, tmp_path):
        """Bundle uses ZIP_DEFLATED compression."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        # Create a file with compressible content
        (tmp_path / ".state.json").write_text('{"version": "1.0"}' * 100)

        result = create_diagnostic_bundle(state)

        assert result is not None
        with zipfile.ZipFile(result, 'r') as zf:
            info = zf.getinfo(".state.json")
            # ZIP_DEFLATED is compression method 8
            assert info.compress_type == zipfile.ZIP_DEFLATED
