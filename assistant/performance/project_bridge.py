from __future__ import annotations

import inspect


def _active_workspace_path():
    candidates = (
        (
            "assistant.knowledge.workspace",
            "get_active_workspace_path",
        ),
        (
            "assistant.knowledge.scanner",
            "get_active_workspace_path",
        ),
        (
            "assistant.perception.workspace",
            "get_active_workspace_path",
        ),
    )

    for module_name, function_name in candidates:
        try:
            module = __import__(
                module_name,
                fromlist=[
                    function_name
                ],
            )

            function = getattr(
                module,
                function_name,
                None,
            )

            if callable(
                function
            ):
                value = function()

                if value:
                    return str(
                        value
                    )

        except Exception:
            continue

    return None


def _call_retrieve_knowledge(
    query: str,
    *,
    workspace_path: str | None,
    limit: int,
):
    from assistant.knowledge.retriever import (
        retrieve_knowledge,
    )

    parameters = (
        inspect.signature(
            retrieve_knowledge
        )
        .parameters
    )

    kwargs = {}

    if "query" in parameters:
        kwargs[
            "query"
        ] = query

    if (
        workspace_path
        and "workspace_path"
        in parameters
    ):
        kwargs[
            "workspace_path"
        ] = workspace_path

    if "limit" in parameters:
        kwargs[
            "limit"
        ] = int(
            limit
        )

    if kwargs:
        return retrieve_knowledge(
            **kwargs
        )

    return retrieve_knowledge(
        query
    )


def _format_item(
    item,
):
    if isinstance(
        item,
        str,
    ):
        return item.strip()

    if not isinstance(
        item,
        dict,
    ):
        return str(
            item
        ).strip()

    path = (
        item.get(
            "relative_path"
        )
        or item.get(
            "path"
        )
        or item.get(
            "file_path"
        )
        or item.get(
            "source"
        )
        or ""
    )

    symbol = (
        item.get(
            "symbol"
        )
        or item.get(
            "name"
        )
        or ""
    )

    content = (
        item.get(
            "content"
        )
        or item.get(
            "text"
        )
        or item.get(
            "chunk"
        )
        or ""
    )

    heading = " | ".join(
        value
        for value in (
            str(
                path
            ).strip(),
            str(
                symbol
            ).strip(),
        )
        if value
    )

    if heading:
        return (
            f"[{heading}]\n"
            f"{str(content).strip()}"
        )

    return str(
        content
    ).strip()


def retrieve_project_evidence(
    user_text: str,
    *,
    limit: int = 6,
    max_characters: int = 7000,
):
    workspace_path = (
        _active_workspace_path()
    )

    try:
        results = (
            _call_retrieve_knowledge(
                user_text,
                workspace_path=
                    workspace_path,
                limit=
                    limit,
            )
        )

    except Exception as error:
        return {
            "success":
                False,

            "workspace_path":
                workspace_path,

            "context":
                "",

            "error":
                str(
                    error
                ),
        }

    if not results:
        return {
            "success":
                True,

            "workspace_path":
                workspace_path,

            "context":
                "",

            "result_count":
                0,
        }

    blocks = []

    used = 0

    for item in list(
        results
    )[
        :max(
            1,
            int(
                limit
            ),
        )
    ]:
        block = (
            _format_item(
                item
            )
        )

        if not block:
            continue

        remaining = (
            max_characters
            - used
        )

        if remaining <= 0:
            break

        block = block[
            :remaining
        ]

        blocks.append(
            block
        )

        used += len(
            block
        )

    return {
        "success":
            True,

        "workspace_path":
            workspace_path,

        "context":
            "\n\n".join(
                blocks
            )
            .strip(),

        "result_count":
            len(
                blocks
            ),
    }


def augment_with_project_evidence(
    user_text: str,
    *,
    allow_project_knowledge: bool,
    limit: int = 6,
    max_characters: int = 7000,
):
    if not allow_project_knowledge:
        return user_text

    evidence = (
        retrieve_project_evidence(
            user_text,
            limit=
                limit,
            max_characters=
                max_characters,
        )
    )

    context = (
        evidence.get(
            "context",
            ""
        )
        .strip()
    )

    if not context:
        return user_text

    workspace = (
        evidence.get(
            "workspace_path"
        )
        or "current workspace"
    )

    return (
        str(
            user_text
            or ""
        )
        .strip()
        + "\n\n"
        + "[E.V.I.E. RETRIEVED PROJECT EVIDENCE]\n"
        + f"Workspace: {workspace}\n"
        + (
            "Use the retrieved source evidence below when answering. "
            "Do not guess a file or function when the evidence supplies one.\n\n"
        )
        + context
    )
