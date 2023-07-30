import base64


def base64_encode(text: str) -> str:
    encodedtext_bytes = base64.b64encode(text.encode("utf-8"))
    encodedtext = str(encodedtext_bytes, "utf-8")
    return encodedtext


def base64_decode(text: str) -> str:
    decodedtext_bytes = base64.b64decode(text)
    decodedtext = str(decodedtext_bytes, "utf-8")
    return decodedtext


def thousands_separators(num):
    """Inserts spaces as thousands separator."""
    return f"{num:,}".replace(",", " ")


def format_time(seconds, milliseconds=False):
    if milliseconds:
        return f"{seconds // 60:02.0f}:{seconds % 60:06.3f}"
    else:
        if not isinstance(seconds, int):
            seconds = round(seconds)
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02}:{seconds:02}"

