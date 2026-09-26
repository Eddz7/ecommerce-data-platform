def validate_columns(fieldnames, expected_columns):
    actual_columns = set(fieldnames or [])
    missing_columns = expected_columns - actual_columns

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )
