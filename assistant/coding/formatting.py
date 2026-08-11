"""
E.V.I.E. - Coding Impact Formatting

Phase 12H
"""


def format_file_impact(analysis):
    lines = [
        f"Impact analysis: {analysis['path']}",
        f"Risk: {analysis['risk']}",
        f"Transitive dependents: {analysis['impact_count']}",
    ]

    if analysis["direct_importers"]:
        lines.append("Direct importers:")
        for node in analysis["direct_importers"]:
            lines.append(f"- {node.path}")

    if analysis["direct_imports"]:
        lines.append("Direct imports:")
        for node in analysis["direct_imports"]:
            lines.append(f"- {node.path}")

    if analysis["tests"]:
        lines.append("Known tests:")
        for node in analysis["tests"]:
            lines.append(f"- {node.path}")

    return "\n".join(lines)


def format_change_scope(scope):
    lines = [
        "Repository change scope",
        f"Risk: {scope['risk']}",
        "Proposed files:",
    ]

    for path in scope["paths"]:
        lines.append(f"- {path}")

    if scope["impacted_nodes"]:
        lines.append("Potentially impacted modules:")
        for item in scope["impacted_nodes"][:30]:
            lines.append(
                f"- {item['node'].path} (depth {item['depth']})"
            )

    if scope["tests"]:
        lines.append("Known relevant tests:")
        for node in scope["tests"]:
            lines.append(f"- {node.path}")

    return "\n".join(lines)
