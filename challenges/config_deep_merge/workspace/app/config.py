def merge_config(base: dict, override: dict) -> dict:
    """Merge override config into base config."""
    result = dict(base)
    result.update(override)
    return result
