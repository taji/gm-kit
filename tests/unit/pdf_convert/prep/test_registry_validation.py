from gm_kit.pdf_convert.prep.registry_errors import (
    PrepRegistryValidationError,
    sanitize_for_log,
)


def test_sanitize_for_log__should_redact_token_values__when_message_contains_secrets() -> None:
    message = (
        "token=abc123 secret=topsecret api_key=xyz789 "
        "credential=opaque password=hunter2 credentials=bundle key=value123"
    )

    sanitized = sanitize_for_log(message)

    assert sanitized == (
        "token=[REDACTED] secret=[REDACTED] "
        "api_key=[REDACTED] credential=[REDACTED] "
        "password=[REDACTED] credentials=[REDACTED] key=[REDACTED]"
    )
    assert "abc123" not in sanitized
    assert "topsecret" not in sanitized
    assert "xyz789" not in sanitized
    assert "opaque" not in sanitized
    assert "hunter2" not in sanitized
    assert "bundle" not in sanitized
    assert "value123" not in sanitized


def test_sanitize_for_log__should_hide_absolute_paths__when_message_contains_local_paths() -> None:
    message = "failed to load /home/todd/private/module.py"

    sanitized = sanitize_for_log(message)

    assert sanitized == "failed to load [REDACTED_PATH]"
    assert "/home/todd/private/module.py" not in sanitized


def test_sanitize_for_log__should_hide_windows_absolute_paths__when_message_contains_local_paths() -> None:
    message = r"failed to load C:\Users\name\secret.txt"

    sanitized = sanitize_for_log(message)

    assert sanitized == "failed to load [REDACTED_PATH]"
    assert r"C:\Users\name\secret.txt" not in sanitized


def test_prep_registry_validation_error__should_include_actionable_fields__when_created() -> None:
    error = PrepRegistryValidationError(
        key="prep.initialize-workspace",
        failure_class="duplicate_phase_order",
        remediation_hint="Use a unique phase order value.",
    )

    rendered = str(error)

    assert "prep.initialize-workspace" in rendered
    assert "duplicate_phase_order" in rendered
    assert "Use a unique phase order value." in rendered


def test_prep_registry_validation_error__should_render_sanitized_message__when_fields_contain_sensitive_values() -> None:
    error = PrepRegistryValidationError(
        key="prep.initialize-workspace",
        failure_class="credential_error token=abc123",
        remediation_hint=(
            r"Rotate api_key=xyz789 and review C:\Users\name\secret.txt "
            r"plus /home/todd/private/module.py"
        ),
    )

    rendered = str(error)

    assert rendered == (
        "Registry validation failed for 'prep.initialize-workspace' "
        "(credential_error token=[REDACTED]). Remediation: Rotate "
        "api_key=[REDACTED] and review [REDACTED_PATH] plus [REDACTED_PATH]"
    )
    assert rendered.count("[REDACTED_PATH]") == 2
    assert "abc123" not in rendered
    assert "xyz789" not in rendered
    assert r"C:\Users\name\secret.txt" not in rendered
    assert "/home/todd/private/module.py" not in rendered
