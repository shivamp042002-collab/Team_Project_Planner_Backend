"""
Reusable, side-effect-free field validators.

These are used by the service layer (users/teams/boards) to enforce the
constraints given in the base-class docstrings (required fields, max
lengths, correct types) without duplicating the same checks in three
different places. Every function raises exceptions.errors.ValidationError
on failure and returns None on success.
"""
from exceptions.errors import ValidationError


def validate_required(value, field_name: str):
    """Raise ValidationError if value is None, or an empty/whitespace-only
    string. Falsy-but-valid values like 0 or False are not in scope here
    since every field in this project is a string or id."""
    if value is None:
        raise ValidationError(f"'{field_name}' is required")
    if isinstance(value, str) and not value.strip():
        raise ValidationError(f"'{field_name}' is required")


def validate_type(value, expected_type, field_name: str):
    """Raise ValidationError if value is not an instance of expected_type."""
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"'{field_name}' must be of type {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )


def validate_max_length(value: str, max_length: int, field_name: str):
    """Raise ValidationError if a string field exceeds max_length characters."""
    if value is not None and len(value) > max_length:
        raise ValidationError(
            f"'{field_name}' must be at most {max_length} characters "
            f"(got {len(value)})"
        )


def validate_choice(value, choices, field_name: str):
    """Raise ValidationError if value is not one of the allowed choices."""
    if value not in choices:
        allowed = ", ".join(sorted(choices))
        raise ValidationError(
            f"'{field_name}' must be one of [{allowed}], got '{value}'"
        )
