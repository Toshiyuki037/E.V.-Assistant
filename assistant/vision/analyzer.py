"""
E.V.I.E. - Visual Input Analyzer

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Prepares temporary E.V.I.E. screenshots for multimodal reasoning.

How It Works:
    1. Validates the temporary screenshot.
    2. Reads source metadata.
    3. Resizes very large captures while preserving aspect ratio.
    4. Encodes the prepared image as base64 JPEG.
    5. Returns multimodal input metadata to brain.py.

Important:
    This module performs image preparation only.
    Reasoning remains centralized in brain.py.

Most Recent Change:
    Added target/window/monitor metadata while preserving the
    single-request multimodal reasoning architecture.
"""

import base64
import io

from pathlib import Path

from PIL import Image


MAX_IMAGE_WIDTH = 2560
MAX_IMAGE_HEIGHT = 1600

JPEG_QUALITY = 88


def validate_screenshot(
    screenshot_path,
):
    """
    Validates a screenshot path and returns a resolved Path.
    """

    if not screenshot_path:

        raise ValueError(
            "No screenshot path was provided."
        )

    path = Path(
        screenshot_path
    ).resolve()

    if not path.exists():

        raise FileNotFoundError(
            (
                "Screenshot does not exist: "
                f"{path}"
            )
        )

    if not path.is_file():

        raise ValueError(
            (
                "Screenshot path is not a file: "
                f"{path}"
            )
        )

    return path


def get_image_metadata(
    screenshot_path,
):
    """
    Returns original screenshot metadata.
    """

    path = validate_screenshot(
        screenshot_path
    )

    with Image.open(
        path
    ) as image:

        width, height = (
            image.size
        )

        image_format = (
            image.format
            or "Unknown"
        )

    return {
        "path":
            str(path),

        "width":
            width,

        "height":
            height,

        "format":
            image_format,
    }


def prepare_image(
    screenshot_path,
):
    """
    Returns prepared JPEG bytes plus prepared dimensions.
    """

    path = validate_screenshot(
        screenshot_path
    )

    with Image.open(
        path
    ) as image:

        image = image.convert(
            "RGB"
        )

        if (
            image.width
            > MAX_IMAGE_WIDTH

            or image.height
            > MAX_IMAGE_HEIGHT
        ):

            image.thumbnail(
                (
                    MAX_IMAGE_WIDTH,
                    MAX_IMAGE_HEIGHT,
                ),

                Image.Resampling.LANCZOS,
            )

        prepared_width = (
            image.width
        )

        prepared_height = (
            image.height
        )

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="JPEG",
            quality=JPEG_QUALITY,
            optimize=True,
        )

        return (
            buffer.getvalue(),
            prepared_width,
            prepared_height,
        )


def encode_image_base64(
    screenshot_path,
):
    """
    Returns base64 JPEG data plus prepared dimensions.
    """

    (
        image_bytes,
        prepared_width,
        prepared_height,
    ) = prepare_image(
        screenshot_path
    )

    encoded = (
        base64.b64encode(
            image_bytes
        )
        .decode(
            "utf-8"
        )
    )

    return (
        encoded,
        prepared_width,
        prepared_height,
    )


def create_image_data_url(
    screenshot_path,
):
    """
    Creates a data URL suitable for multimodal input.
    """

    (
        encoded,
        prepared_width,
        prepared_height,
    ) = encode_image_base64(
        screenshot_path
    )

    return (
        (
            "data:image/jpeg;base64,"
            f"{encoded}"
        ),
        prepared_width,
        prepared_height,
    )


def build_visual_input(
    visual_context,
):
    """
    Converts routed visual context into brain-ready multimodal input.
    """

    if not visual_context:

        return None

    screenshot_path = (
        visual_context.get(
            "screenshot_path"
        )
    )

    if not screenshot_path:

        return None

    metadata = (
        get_image_metadata(
            screenshot_path
        )
    )

    (
        image_url,
        prepared_width,
        prepared_height,
    ) = create_image_data_url(
        screenshot_path
    )

    return {
        "image_url":
            image_url,

        "screenshot_path":
            screenshot_path,

        "source":
            visual_context.get(
                "source",
                "unknown",
            ),

        "requested_target":
            visual_context.get(
                "requested_target",
                "unknown",
            ),

        "active_window_title":
            visual_context.get(
                "active_window_title"
            ),

        "monitor_index":
            visual_context.get(
                "monitor_index"
            ),

        "fresh":
            visual_context.get(
                "fresh",
                False,
            ),

        "temporary":
            visual_context.get(
                "temporary",
                True,
            ),

        "width":
            metadata[
                "width"
            ],

        "height":
            metadata[
                "height"
            ],

        "prepared_width":
            prepared_width,

        "prepared_height":
            prepared_height,
    }


if __name__ == "__main__":

    from .context import (
        capture_visual_context,
    )

    from .lifecycle import (
        delete_visual_artifact,
    )

    print(
        "E.V.I.E. Visual Input Analyzer"
    )

    print(
        "-------------------------------"
    )

    context = None

    try:

        test_message = (
            "Explain the code I currently have visible."
        )

        context = (
            capture_visual_context(
                test_message
            )
        )

        if not context:

            print(
                "No visual context captured."
            )

            raise SystemExit(0)

        visual_input = (
            build_visual_input(
                context
            )
        )

        print(
            "Screenshot:",
            visual_input[
                "screenshot_path"
            ],
        )

        print(
            "Source:",
            visual_input[
                "source"
            ],
        )

        print(
            "Requested target:",
            visual_input[
                "requested_target"
            ],
        )

        print(
            "Active window:",
            visual_input[
                "active_window_title"
            ],
        )

        print(
            "Original resolution:",
            (
                f"{visual_input['width']}x"
                f"{visual_input['height']}"
            ),
        )

        print(
            "Prepared resolution:",
            (
                f"{visual_input['prepared_width']}x"
                f"{visual_input['prepared_height']}"
            ),
        )

        print(
            "Fresh:",
            visual_input[
                "fresh"
            ],
        )

        print(
            "Image encoded:",
            bool(
                visual_input[
                    "image_url"
                ]
            ),
        )

        print(
            "Encoded length:",
            len(
                visual_input[
                    "image_url"
                ]
            ),
        )

    finally:

        if context:

            deleted = (
                delete_visual_artifact(
                    context.get(
                        "screenshot_path"
                    )
                )
            )

            print(
                "Temporary screenshot deleted:",
                deleted,
            )
