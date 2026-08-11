"""
E.V.I.E. - Workflow Package

Phase 11

Important:
This package intentionally performs no eager imports.

Background services such as the scheduler must be able to start
without loading:
    - E.V.I.E. reasoning
    - semantic memory
    - sentence transformers
    - speech systems
    - browser systems

Import workflow functionality directly from the required module.

Examples:

    from assistant.workflows.protocols import run_protocol

    from assistant.workflows.controller import run_workflow

    from assistant.workflows.schedules import create_schedule
"""