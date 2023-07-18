import base64


def base64_encode(text: str) -> str:
    encodedtext_bytes = base64.b64encode(text.encode("utf-8"))
    encodedtext = str(encodedtext_bytes, "utf-8")
    return encodedtext


def base64_decode(text: str) -> str:
    decodedtext_bytes = base64.b64decode(text)
    decodedtext = str(decodedtext_bytes, "utf-8")
    return decodedtext

