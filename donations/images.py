from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_DIMENSION = 1600  


class ImageCheckError(ValueError):
    """Raised when an upload is not an acceptable photo."""


def check_and_clean_image(uploaded):
    """Check type and size, fix rotation, shrink, and remove metadata such as GPS location."""
    if uploaded.size > MAX_UPLOAD_BYTES:
        raise ImageCheckError(f"{uploaded.name} is larger than 5 MB.")

    try:
        image = Image.open(uploaded)
        image_format = image.format
        image.load()
    except (UnidentifiedImageError, OSError):
        raise ImageCheckError(f"{uploaded.name} is not a valid image.")

    if image_format not in ALLOWED_FORMATS:
        raise ImageCheckError(f"{uploaded.name} must be a JPEG, PNG or WebP image.")

    # Turn the photo the right way up before the metadata is dropped.
    image = ImageOps.exif_transpose(image)
    image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))

    output = BytesIO()
    if image_format == "JPEG":
        image.convert("RGB").save(output, "JPEG", quality=85, optimize=True)
    elif image_format == "PNG":
        image.save(output, "PNG", optimize=True)
    else:
        image.save(output, "WEBP", quality=85)

    return ContentFile(output.getvalue(), name=f"photo.{ALLOWED_FORMATS[image_format]}")