"""
E.V.I.E. - Phase 11E Protocol Templates
"""

from __future__ import annotations

from .protocols import create_protocol


def install_default_protocols(overwrite: bool = False):
    installed = []

    installed.append(
        create_protocol(
            protocol_id="morning",
            name="Morning Protocol",
            goal="Collect the user's morning context for a concise briefing.",
            description=(
                "Reusable morning workflow. Phase 11F can schedule this; "
                "Phase 11G will add natural-language protocol control."
            ),
            default_variables={
                "location": "Honolulu",
            },
            steps=[
                {
                    "step_id": "weather",
                    "description": "Read current weather.",
                    "tool_name": "integration_execute",
                    "arguments": {
                        "capability": "weather.current",
                        "provider": "weather",
                        "account_id": "public",
                        "routing_mode": "explicit_account",
                        "arguments": {
                            "location": "{{ variables.location }}"
                        },
                    },
                    "output_key": "weather",
                },
            ],
            overwrite=overwrite,
        )
    )

    installed.append(
        create_protocol(
            protocol_id="research",
            name="Research Protocol",
            goal="Collect current engineering project context for research planning.",
            description=(
                "Reusable research context workflow. Add Notion/project-specific "
                "steps as desired without changing the protocol subsystem."
            ),
            default_variables={
                "repo": "E.V.-Assistant",
            },
            steps=[
                {
                    "step_id": "commits",
                    "description": "Read latest repository commits.",
                    "tool_name": "integration_execute",
                    "arguments": {
                        "capability": "github.commits",
                        "provider": "github",
                        "account_id": "primary",
                        "routing_mode": "explicit_account",
                        "arguments": {
                            "repo": "{{ variables.repo }}"
                        },
                    },
                    "output_key": "github_commits",
                },
            ],
            overwrite=overwrite,
        )
    )

    return installed


if __name__ == "__main__":
    protocols = install_default_protocols(overwrite=True)
    for protocol in protocols:
        print(protocol["protocol_id"], "-", protocol["name"])
