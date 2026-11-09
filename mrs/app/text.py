def normalize_line_endings(text: str) -> str:
    """Collapses CRLF/CR to bare LF.

    HTML forms normalize textarea line breaks to CRLF on submission (per
    the HTML spec, not a browser quirk), but body-rendering code splits on
    a bare "\\n\\n" to find paragraph breaks. Without this, CRLF-separated
    text never splits -- the raw \\r\\n characters just collapse to
    whitespace in HTML, squashing every paragraph into one run-on block.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")
