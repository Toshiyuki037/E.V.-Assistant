"""
E.V.I.E. - Monitor Awareness

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Detects connected physical monitors for E.V.I.E.'s vision system.

Most Recent Change:
    Uses the current MSS interface and exposes monitor geometry for
    intelligent visual targeting.
"""

import mss


def get_monitors():
    """
    Returns physical monitors only.

    MSS monitor 0 represents the combined virtual desktop.
    Physical monitors begin at index 1.
    """

    monitors = []

    with mss.MSS() as screen:

        for index, monitor in enumerate(
            screen.monitors[1:],
            start=1,
        ):

            monitors.append(
                {
                    "index":
                        index,

                    "left":
                        monitor["left"],

                    "top":
                        monitor["top"],

                    "width":
                        monitor["width"],

                    "height":
                        monitor["height"],
                }
            )

    return monitors


if __name__ == "__main__":

    print(
        "E.V.I.E. Monitor Awareness"
    )

    print(
        "---------------------------"
    )

    monitors = get_monitors()

    print(
        "Monitors detected:",
        len(monitors),
    )

    for monitor in monitors:

        print()

        print(
            f"Monitor {monitor['index']}"
        )

        print(
            "Position:",
            monitor["left"],
            monitor["top"],
        )

        print(
            "Resolution:",
            (
                f"{monitor['width']}x"
                f"{monitor['height']}"
            ),
        )
