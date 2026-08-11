"""
E.V.I.E. - Python Repository Parser

Phase 12C - Import Graph Fix

Extracts module structure and preserves enough information to resolve:
    import assistant.foo
    from assistant import foo
    from . import foo
    from .foo import bar
    from ..foo import bar

No code is executed.
"""

from __future__ import annotations

import ast
from pathlib import Path


def module_name_from_path(relative_path: str):
    path = relative_path.replace("\\", "/")

    if not path.endswith(".py"):
        return ""

    path = path[:-3]

    if path == "__init__":
        return ""

    if path.endswith("/__init__"):
        path = path[:-9].rstrip("/")

    return path.replace("/", ".")


def parse_python_file(
    path: Path,
    *,
    root: Path,
):
    relative = str(
        path.relative_to(root)
    ).replace("\\", "/")

    source = path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    try:
        tree = ast.parse(
            source,
            filename=relative,
        )
    except SyntaxError as error:
        return {
            "path": relative,
            "module": module_name_from_path(relative),
            "imports": [],
            "classes": [],
            "functions": [],
            "syntax_error": str(error),
        }

    imports = []
    classes = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "kind": "import",
                    "module": alias.name,
                    "level": 0,
                    "names": [],
                })

        elif isinstance(node, ast.ImportFrom):
            imports.append({
                "kind": "from",
                "module": node.module or "",
                "level": int(node.level or 0),
                "names": [
                    alias.name
                    for alias in node.names
                ],
            })

        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "lineno": getattr(node, "lineno", 0),
            })

        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            functions.append({
                "name": node.name,
                "lineno": getattr(node, "lineno", 0),
                "async": isinstance(
                    node,
                    ast.AsyncFunctionDef,
                ),
            })

    return {
        "path": relative,
        "module": module_name_from_path(relative),
        "imports": imports,
        "classes": classes,
        "functions": functions,
        "syntax_error": "",
    }
