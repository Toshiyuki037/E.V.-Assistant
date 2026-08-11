"""
E.V.I.E. - Coding Intelligence

Phase 12H public interface.
"""

from .impact import analyze_file_impact, analyze_change_scope
from .architecture import summarize_repository_architecture

from .models import (
    EngineeringEdit,
    EngineeringPlan,
)

from .planner import (
    plan_engineering_change,
)

from .controller import (
    execute_engineering_plan,
)

from .approval import (
    approve_and_commit_engineering_transaction,
)

from .documentation import (
    build_engineering_documentation_note,
)

from .integration import handle_coding_message
from .request_planner import plan_coding_request
from .discovery import discover_candidate_paths
