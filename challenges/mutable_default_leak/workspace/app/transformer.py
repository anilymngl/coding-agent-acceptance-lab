def extract_hashtags(text: str, tags: list[str] = []) -> list[str]:
    """Extract hashtags from text."""
    for word in text.split():
        if word.startswith("#"):
            tags.append(word)
    return tags
