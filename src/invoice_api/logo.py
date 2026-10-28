import io

from reportlab.lib.utils import ImageReader

MAX_BYTES = 2 * 1024 * 1024


class LogoError(ValueError):
    pass


def load_logo(data: bytes) -> ImageReader:
    if len(data) > MAX_BYTES:
        raise LogoError("logo exceeds 2 MB")
    if not (data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"\xff\xd8\xff")):
        raise LogoError("logo must be a PNG or JPEG image")
    try:
        img = ImageReader(io.BytesIO(data))
        img.getSize()
    except Exception as e:  # corrupt image
        raise LogoError(f"unreadable logo image: {e}") from e
    return img
