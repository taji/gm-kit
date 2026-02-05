"""Unit tests for pdf_convert error helpers."""

from gm_kit.pdf_convert.errors import ErrorMessages, ExitCode, format_error, get_exit_code_for_error


def test_format_error__should_include_context__when_context_provided():
    """format_error includes context and suggestion."""
    message = format_error(ErrorMessages.PDF_NOT_FOUND, "/tmp/missing.pdf")
    assert (
        message
        == "ERROR: Cannot open PDF - file not found or corrupted (/tmp/missing.pdf)\n"
        "  Check the file path and ensure the file exists"
    )


def test_format_error__should_omit_context__when_context_missing():
    """format_error omits context when none provided."""
    message = format_error(ErrorMessages.NO_TOC)
    assert message == "WARNING: No TOC found - hierarchy may be incomplete"


def test_get_exit_code_for_error__should_return_user_abort__when_abort_prefix():
    """ABORT errors map to USER_ABORT."""
    exit_code = get_exit_code_for_error(ErrorMessages.USER_CANCELLED)
    assert exit_code == ExitCode.USER_ABORT


def test_get_exit_code_for_error__should_return_dependency_error__when_installation_message():
    """Installation/module errors map to DEPENDENCY_ERROR."""
    exit_code = get_exit_code_for_error(ErrorMessages.DEPENDENCY_MISSING)
    assert exit_code == ExitCode.DEPENDENCY_ERROR


def test_get_exit_code_for_error__should_return_default_file_error__when_no_match():
    """Unknown errors default to FILE_ERROR."""
    exit_code = get_exit_code_for_error(("ERROR", "Something went wrong", None))
    assert exit_code == ExitCode.FILE_ERROR


def test_get_exit_code_for_error__should_return_file_error__when_file_keywords_present():
    """File-related messages map to FILE_ERROR."""
    exit_code = get_exit_code_for_error(("ERROR", "Cannot open file", None))
    assert exit_code == ExitCode.FILE_ERROR


def test_get_exit_code_for_error__should_return_pdf_error__when_pdf_keywords_present():
    """PDF-related messages map to PDF_ERROR."""
    exit_code = get_exit_code_for_error(("ERROR", "Scanned PDF detected", None))
    assert exit_code == ExitCode.PDF_ERROR


def test_get_exit_code_for_error__should_return_state_error__when_state_keywords_present():
    """State-related messages map to STATE_ERROR."""
    exit_code = get_exit_code_for_error(("ERROR", "State file missing", None))
    assert exit_code == ExitCode.STATE_ERROR
