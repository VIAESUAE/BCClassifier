from __future__ import annotations

import uuid
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np

from app.config import get_settings


def _ensure_upload_dir() -> Path:
    path = Path(get_settings().upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_upload(data: bytes, suffix: str = ".jpg") -> Path:
    dest = _ensure_upload_dir() / f"{uuid.uuid4().hex}{suffix}"
    dest.write_bytes(data)
    return dest


def preprocess_card_image(image_path: Path) -> Tuple[Path, dict]:
    """Reduce glare/overexposure and attempt perspective crop of the card region."""
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError("Could not read uploaded image")

    meta = {"steps": []}
    working = img.copy()

    # Mild glare / highlight compression via CLAHE on luminance
    lab = cv2.cvtColor(working, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    working = cv2.cvtColor(cv2.merge([l2, a, b]), cv2.COLOR_LAB2BGR)
    meta["steps"].append("clahe")

    # Denoise lightly
    working = cv2.bilateralFilter(working, d=5, sigmaColor=50, sigmaSpace=50)
    meta["steps"].append("bilateral")

    cropped, found = _try_perspective_crop(working)
    if found:
        working = cropped
        meta["steps"].append("perspective_crop")
    else:
        meta["steps"].append("full_frame")

    out = _ensure_upload_dir() / f"{image_path.stem}_processed.jpg"
    cv2.imwrite(str(out), working, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    return out, meta


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def _try_perspective_crop(image: np.ndarray) -> Tuple[np.ndarray, bool]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 50, 150)
    edged = cv2.dilate(edged, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    h, w = gray.shape
    min_area = h * w * 0.12

    for cnt in contours:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4 and cv2.contourArea(approx) >= min_area:
            pts = approx.reshape(4, 2).astype("float32")
            rect = _order_points(pts)
            (tl, tr, br, bl) = rect
            width_a = np.linalg.norm(br - bl)
            width_b = np.linalg.norm(tr - tl)
            height_a = np.linalg.norm(tr - br)
            height_b = np.linalg.norm(tl - bl)
            max_w = int(max(width_a, width_b))
            max_h = int(max(height_a, height_b))
            if max_w < 80 or max_h < 40:
                continue
            dst = np.array(
                [[0, 0], [max_w - 1, 0], [max_w - 1, max_h - 1], [0, max_h - 1]],
                dtype="float32",
            )
            matrix = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(image, matrix, (max_w, max_h))
            return warped, True
    return image, False
