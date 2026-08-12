"""
E.V.I.E. - Local Camera Discovery & Capture

Phase 13F

Uses OpenCV for structured local camera probing and still-frame capture.

Long-running video streaming belongs to later perception/device phases.
"""

from __future__ import annotations

from pathlib import Path

from .media_models import (
    CameraDeviceInfo,
    CaptureResult,
)

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None


class CameraBackendUnavailable(RuntimeError):
    pass


def _require_opencv():
    if cv2 is None:
        raise CameraBackendUnavailable(
            "Phase 13F camera support requires OpenCV. "
            "Install it with: python -m pip install opencv-python"
        )


def _open_camera(
    index: int,
):
    _require_opencv()

    camera_index = int(
        index
    )

    if camera_index < 0:
        raise ValueError(
            "Camera index must be zero or greater."
        )

    backend = (
        cv2.CAP_DSHOW
        if hasattr(
            cv2,
            "CAP_DSHOW",
        )
        else 0
    )

    capture = cv2.VideoCapture(
        camera_index,
        backend,
    )

    return capture


def inspect_camera(
    index: int,
) -> CameraDeviceInfo:
    capture = _open_camera(
        index
    )

    try:
        available = bool(
            capture.isOpened()
        )

        if not available:
            return CameraDeviceInfo(
                index=int(index),
                available=False,
            )

        width = int(
            capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
            or 0
        )

        height = int(
            capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
            or 0
        )

        fps = float(
            capture.get(
                cv2.CAP_PROP_FPS
            )
            or 0.0
        )

        backend_name = ""

        try:
            backend_name = str(
                capture.getBackendName()
            )
        except Exception:
            backend_name = ""

        return CameraDeviceInfo(
            index=int(index),
            available=True,
            width=width,
            height=height,
            fps=fps,
            backend=backend_name,
        )

    finally:
        capture.release()


def list_cameras(
    *,
    max_index: int = 5,
) -> list[CameraDeviceInfo]:
    maximum = max(
        0,
        int(max_index),
    )

    result = []

    for index in range(
        maximum
    ):
        info = inspect_camera(
            index
        )

        if info.available:
            result.append(
                info
            )

    return result


def capture_camera_frame(
    path: str,
    *,
    camera_index: int = 0,
) -> CaptureResult:
    capture = _open_camera(
        camera_index
    )

    target = Path(
        path
    ).resolve(
        strict=False
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        if not capture.isOpened():
            raise RuntimeError(
                f"Camera {camera_index} could not be opened."
            )

        ok, frame = capture.read()

        if (
            not ok
            or frame is None
        ):
            raise RuntimeError(
                f"Camera {camera_index} did not return a frame."
            )

        saved = bool(
            cv2.imwrite(
                str(target),
                frame,
            )
        )

    finally:
        capture.release()

    verified = (
        saved
        and target.exists()
        and target.stat().st_size > 0
    )

    return CaptureResult(
        kind="camera_frame",
        path=str(target),
        success=verified,
        detail=(
            "Camera frame captured."
            if verified
            else "Camera frame capture could not be verified."
        ),
    )
