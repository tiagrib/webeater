def cleanup_whitespace(text):
    """
    Clean up excessive whitespace in the text.
    """
    while "  " in text or "\n\n" in text:
        while "  " in text:
            text = text.replace("  ", " ")
        text = text.strip()

        while "\n\n" in text:
            text = text.replace("\n\n", "\n")

        text = text.strip()

    return text
