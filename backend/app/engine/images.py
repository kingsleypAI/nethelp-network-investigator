"""PingPlotter / traceroute screenshot analysis (OpenCV).

Screenshots can't be OCR'd reliably without a heavy stack, so this module does
two practical things for the demo/production scaffold:

1. Basic visual heuristics with OpenCV (image dimensions, red/amber pixel ratio
   — PingPlotter colours problem hops red, which is a useful coarse signal).
2. A clean extension point: drop OCR (pytesseract/easyocr) results into
   ``ocr_text`` and the main text engine will parse hops/loss automatically.
"""
from __future__ import annotations

from typing import Optional

try:
    import cv2  # noqa
    import numpy as np
    _CV = True
except Exception:  # pragma: no cover - OpenCV optional at import time
    _CV = False


def analyse_image(path: str) -> dict:
    """Return coarse visual signals from a network screenshot."""
    if not _CV:
        return {"ok": False, "reason": "OpenCV not available", "ocr_text": ""}
    img = cv2.imread(path)
    if img is None:
        return {"ok": False, "reason": "Could not read image", "ocr_text": ""}

    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    total = h * w

    red1 = cv2.inRange(hsv, (0, 90, 90), (10, 255, 255))
    red2 = cv2.inRange(hsv, (170, 90, 90), (180, 255, 255))
    amber = cv2.inRange(hsv, (15, 90, 90), (35, 255, 255))
    red_ratio = float((red1.sum() + red2.sum()) / 255 / total)
    amber_ratio = float(amber.sum() / 255 / total)

    signal = "none"
    if red_ratio > 0.01:
        signal = "problem-hops-likely"   # PingPlotter marks loss/high latency red
    elif amber_ratio > 0.02:
        signal = "warning-hops-likely"

    return {
        "ok": True,
        "width": w,
        "height": h,
        "red_ratio": round(red_ratio, 4),
        "amber_ratio": round(amber_ratio, 4),
        "visual_signal": signal,
        "ocr_text": "",  # plug OCR output here to feed the text engine
        "note": "Coarse visual scan. For full hop/loss extraction, enable OCR and "
                "pass ocr_text into the /analyze endpoint.",
    }
