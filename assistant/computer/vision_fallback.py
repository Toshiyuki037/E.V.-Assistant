from __future__ import annotations
from .vision_models import VisualTarget

def normalize_visual_target(payload: dict) -> VisualTarget:
    required = ("label", "x", "y", "width", "height")
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Visual target missing fields: {missing}")

    width = int(payload["width"])
    height = int(payload["height"])

    if width <= 0 or height <= 0:
        raise ValueError("Visual target dimensions must be positive.")

    confidence = float(payload.get("confidence", 0.0))
    confidence = max(0.0, min(1.0, confidence))

    return VisualTarget(
        label=str(payload["label"]),
        x=int(payload["x"]),
        y=int(payload["y"]),
        width=width,
        height=height,
        confidence=confidence,
        source=str(payload.get("source", "vision")),
    )

def validate_visual_target(
    target: VisualTarget,
    *,
    screen_width: int,
    screen_height: int,
    min_confidence: float = 0.70,
) -> None:
    if target.confidence < float(min_confidence):
        raise ValueError(
            f"Visual target confidence too low: {target.confidence:.3f}"
        )

    cx, cy = target.center

    if not (0 <= cx < int(screen_width) and 0 <= cy < int(screen_height)):
        raise ValueError(
            f"Visual target center is outside the capture bounds: {(cx, cy)}"
        )

def choose_visual_target(
    candidates: list[VisualTarget],
    *,
    min_confidence: float = 0.70,
) -> VisualTarget:
    valid = [
        item
        for item in candidates
        if item.confidence >= float(min_confidence)
    ]

    if not valid:
        raise LookupError("No visual target met the confidence threshold.")

    valid.sort(key=lambda item: item.confidence, reverse=True)

    if len(valid) > 1:
        gap = valid[0].confidence - valid[1].confidence
        if gap < 0.05:
            raise LookupError(
                "Visual target is ambiguous; top candidates are too close."
            )

    return valid[0]
