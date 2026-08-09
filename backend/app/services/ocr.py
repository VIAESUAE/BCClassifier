from __future__ import annotations

from pathlib import Path
from typing import Optional

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR

        _engine = RapidOCR()
    return _engine


def run_ocr(image_path: Path) -> str:
    """Extract text lines from a business card image."""
    engine = _get_engine()
    result, _ = engine(str(image_path))
    if not result:
        return ""
    lines = [item[1] for item in result if item and len(item) > 1 and item[1]]
    return "\n".join(lines).strip()


def ocr_or_empty(image_path: Path) -> tuple[str, Optional[str]]:
    try:
        text = run_ocr(image_path)
        return text, None
    except Exception as exc:  # noqa: BLE001 — surface as warning to UI
        return "", f"OCR failed: {exc}"
