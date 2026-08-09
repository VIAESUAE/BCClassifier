from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from app.schemas import CardFields


@dataclass
class PreviewSession:
    preview_id: str
    original_path: Path
    processed_path: Path
    raw_ocr: str
    extracted: CardFields
    warnings: list


_PREVIEW_STORE: "OrderedDict[str, PreviewSession]" = OrderedDict()
_MAX = 64


def put_preview(session: PreviewSession) -> None:
    _PREVIEW_STORE[session.preview_id] = session
    while len(_PREVIEW_STORE) > _MAX:
        _PREVIEW_STORE.popitem(last=False)


def get_preview(preview_id: str) -> Optional[PreviewSession]:
    return _PREVIEW_STORE.get(preview_id)


def pop_preview(preview_id: str) -> Optional[PreviewSession]:
    return _PREVIEW_STORE.pop(preview_id, None)
