"""Tests for conversion logging configuration (E4-07a-i)."""

import logging
import sys

from gm_kit.pdf_convert.logging_config import (
    ConversionLogFormatter,
    TeeOutput,
    reset_output_streams,
    setup_conversion_logging,
)


class TestTeeOutput:
    """Tests for TeeOutput class."""

    def test_tee_output_writes_to_both_streams(self, tmp_path):
        """TeeOutput should write to both original stream and log file."""
        log_path = tmp_path / "test.log"
        original = sys.stdout

        try:
            tee = TeeOutput(original, log_path)
            tee.write("test message\n")

            # Check log file
            assert log_path.exists()
            assert "test message" in log_path.read_text(encoding="utf-8")
        finally:
            pass  # Original stdout unchanged

    def test_tee_output_handles_write_errors_gracefully(self, tmp_path):
        """TeeOutput should continue if log file can't be written."""
        log_path = tmp_path / "nonexistent" / "test.log"
        original = sys.stdout

        tee = TeeOutput(original, log_path)
        # Should not raise even though path doesn't exist
        result = tee.write("test message\n")
        assert result == len("test message\n")

    def test_tee_output_delegates_flush(self, tmp_path):
        """TeeOutput should delegate flush to original stream."""
        log_path = tmp_path / "test.log"

        class MockStream:
            flushed = False

            def write(self, data):
                return len(data)

            def flush(self):
                self.flushed = True

        mock = MockStream()
        tee = TeeOutput(mock, log_path)
        tee.flush()

        assert mock.flushed


class TestConversionLogFormatter:
    """Tests for ConversionLogFormatter."""

    def test_formatter_includes_level_and_message(self):
        """Formatter should include level name and message."""
        formatter = ConversionLogFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert "INFO" in formatted
        assert "Test message" in formatted


class TestSetupConversionLogging:
    """Tests for setup_conversion_logging function."""

    def test_creates_log_file_with_utf8_encoding(self, tmp_path):
        """Should create conversion.log with UTF-8 encoding."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        logger = setup_conversion_logging(output_dir)

        log_path = output_dir / "conversion.log"
        assert log_path.exists()

        # Check it's UTF-8 by writing Unicode
        logger.info("Test message with unicode: ✓")

        content = log_path.read_text(encoding="utf-8")
        assert "✓" in content

    def test_clears_existing_log_file(self, tmp_path):
        """Should clear existing log file on setup."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        log_path = output_dir / "conversion.log"
        log_path.write_text("old content", encoding="utf-8")

        setup_conversion_logging(output_dir)

        content = log_path.read_text(encoding="utf-8")
        assert "old content" not in content
        assert "Conversion logging initialized" in content

    def test_redirects_stdout_and_stderr(self, tmp_path):
        """Should redirect stdout and stderr to TeeOutput."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            setup_conversion_logging(output_dir)

            assert isinstance(sys.stdout, TeeOutput)
            assert isinstance(sys.stderr, TeeOutput)

            print("stdout test")
            print("stderr test", file=sys.stderr)

            log_content = (output_dir / "conversion.log").read_text(encoding="utf-8")
            assert "stdout test" in log_content
            assert "stderr test" in log_content
        finally:
            reset_output_streams()

        # Verify streams are restored
        assert sys.stdout is original_stdout
        assert sys.stderr is original_stderr


class TestResetOutputStreams:
    """Tests for reset_output_streams function."""

    def test_restores_original_streams(self, tmp_path):
        """Should restore original stdout and stderr."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        original_stdout = sys.stdout
        original_stderr = sys.stderr

        setup_conversion_logging(output_dir)
        reset_output_streams()

        assert sys.stdout is original_stdout
        assert sys.stderr is original_stderr

    def test_handles_non_tee_streams(self):
        """Should not error if streams are not TeeOutput."""
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            reset_output_streams()
            assert sys.stdout is original_stdout
            assert sys.stderr is original_stderr
        finally:
            pass
