from exceptions.errors import ValidationError


def validate_required(value, field_name: str):
    if value is None:
        raise ValidationError(f"'{field_name}' is required")
    if isinstance(value, str) and not value.strip():
        raise ValidationError(f"'{field_name}' is required")


def validate_type(value, expected_type, field_name: str):
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"'{field_name}' must be of type {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )


def validate_max_length(value: str, max_length: int, field_name: str):
    if value is not None and len(value) > max_length:
        raise ValidationError(
            f"'{field_name}' must be at most {max_length} characters "
            f"(got {len(value)})"
        )


def validate_choice(value, choices, field_name: str):
    if value not in choices:
        allowed = ", ".join(sorted(choices))
        raise ValidationError(
            f"'{field_name}' must be one of [{allowed}], got '{value}'"
        )
