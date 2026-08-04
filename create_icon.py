"""Build a multi-resolution Windows icon.ico for PCFIX."""
from PIL import Image
import os

SOURCE_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "assets", "pcfix_logo_source.png"),
    os.path.join(os.path.dirname(__file__), "pcfix_logo_source.png"),
]
SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def _find_source():
    for path in SOURCE_CANDIDATES:
        if os.path.isfile(path):
            return path
    return None


def create_icon(source_path=None, output_path="icon.ico"):
    source_path = source_path or _find_source()
    if not source_path:
        raise FileNotFoundError("No logo source PNG found. Place pcfix_logo_source.png in assets/.")

    src = Image.open(source_path).convert("RGBA")
    w, h = src.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    src = src.crop((left, top, left + side, top + side))
    base = src.resize((256, 256), Image.Resampling.LANCZOS)
    base.save(output_path, format="ICO", sizes=SIZES)
    print(f"Icon '{output_path}' created from '{source_path}' ({os.path.getsize(output_path)} bytes).")


if __name__ == "__main__":
    create_icon()
