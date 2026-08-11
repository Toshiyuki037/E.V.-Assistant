"""
E.V.I.E. - Workflow Presentation

Phase 11H

Purpose:
Turn workflow results into useful user-facing output rather than merely
reporting step status.

The formatter is deterministic and does not require the LLM.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Generic Helpers
# ---------------------------------------------------------------------------

def _unwrap_integration_result(
    value: Any,
):
    """
    Phase 9 integration_execute results usually contain:
        {
            "success": True,
            "capability": "...",
            "evidence": [
                {
                    "data": {...}
                }
            ]
        }

    This helper returns the first evidence data payload when available.
    """

    if not isinstance(
        value,
        dict,
    ):
        return value

    evidence = (
        value.get(
            "evidence",
            []
        )
        or []
    )

    if (
        isinstance(
            evidence,
            list,
        )
        and evidence
        and isinstance(
            evidence[0],
            dict,
        )
    ):
        data = (
            evidence[0]
            .get(
                "data"
            )
        )

        if data is not None:
            return data

    return value


def _find_first(
    data: dict,
    keys: list[str],
):
    for key in keys:
        if key in data:
            return data[
                key
            ]
    return None


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------

def format_weather_output(
    raw,
):
    data = _unwrap_integration_result(
        raw
    )

    if not isinstance(
        data,
        dict,
    ):
        return (
            "Weather data was collected successfully."
        )

    location = _find_first(
        data,
        [
            "resolved_location",
            "location",
            "name",
            "city",
        ],
    )

    temperature = _find_first(
        data,
        [
            "temperature_f",
            "temperature",
            "temp_f",
            "temp",
        ],
    )

    feels_like = _find_first(
        data,
        [
            "feels_like_f",
            "feels_like",
            "apparent_temperature",
        ],
    )

    condition = _find_first(
        data,
        [
            "condition",
            "conditions",
            "weather",
            "description",
        ],
    )

    humidity = _find_first(
        data,
        [
            "humidity",
            "humidity_percent",
        ],
    )

    pieces = []

    if location:
        pieces.append(
            str(
                location
            )
        )

    if temperature is not None:
        pieces.append(
            f"{temperature}°F"
        )

    if condition:
        pieces.append(
            str(
                condition
            )
        )

    if feels_like is not None:
        pieces.append(
            f"feels like {feels_like}°F"
        )

    if humidity is not None:
        pieces.append(
            f"humidity {humidity}%"
        )

    if pieces:
        return (
            "Weather: "
            + ", ".join(
                pieces
            )
            + "."
        )

    return (
        "Weather data was collected successfully."
    )


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

def format_github_commits_output(
    raw,
):
    data = _unwrap_integration_result(
        raw
    )

    if isinstance(
        data,
        dict,
    ):
        commits = (
            data.get(
                "commits"
            )
            or data.get(
                "results"
            )
            or data.get(
                "items"
            )
        )
    else:
        commits = data

    if not isinstance(
        commits,
        list,
    ):
        return (
            "GitHub commit data was collected successfully."
        )

    if not commits:
        return (
            "No recent GitHub commits were returned."
        )

    lines = [
        "Recent GitHub commits:"
    ]

    for commit in commits[
        :5
    ]:
        if not isinstance(
            commit,
            dict,
        ):
            continue

        sha = (
            commit.get(
                "sha"
            )
            or commit.get(
                "short_sha"
            )
            or ""
        )

        if sha:
            sha = str(
                sha
            )[
                :7
            ]

        message = (
            commit.get(
                "message"
            )
            or commit.get(
                "title"
            )
            or "commit"
        )

        prefix = (
            f"{sha} — "
            if sha
            else ""
        )

        lines.append(
            f"- {prefix}{message}"
        )

    return "\n".join(
        lines
    )


# ---------------------------------------------------------------------------
# Full Workflow
# ---------------------------------------------------------------------------

def format_workflow_outputs(
    run,
):
    lines = [
        f"{run.workflow_name} completed."
        if run.status == "completed"
        else (
            f"{run.workflow_name} status: "
            f"{run.status}."
        )
    ]

    outputs = (
        run.outputs
        or {}
    )

    if "weather" in outputs:
        lines.append(
            format_weather_output(
                outputs[
                    "weather"
                ]
            )
        )

    if "github_commits" in outputs:
        lines.append(
            format_github_commits_output(
                outputs[
                    "github_commits"
                ]
            )
        )

    known = {
        "weather",
        "github_commits",
    }

    unknown_outputs = [
        key
        for key
        in outputs
        if key not in known
    ]

    if unknown_outputs:
        lines.append(
            (
                "Additional workflow outputs: "
                + ", ".join(
                    unknown_outputs
                )
                + "."
            )
        )

    if run.awaiting_user_reason:
        lines.append(
            (
                "Needs input: "
                f"{run.awaiting_user_reason}"
            )
        )

    if run.pending_action:
        description = (
            run.pending_action.get(
                "description"
            )
            or "workflow action"
        )

        risk = (
            run.pending_action.get(
                "risk"
            )
            or "unknown"
        )

        lines.append(
            (
                f"Pending approval: "
                f"{description} "
                f"(risk: {risk})."
            )
        )

    return "\n".join(
        lines
    )
