"""E.V.I.E. system awareness, health, diagnostics, maintenance, repair, backup, and certification package."""

from .manifest import (
    EVIE_VERSION,
    SYSTEM_MANIFEST,
    get_system_manifest,
    get_capability,
    list_capabilities,
)

from .health import (
    HEALTHY,
    DEGRADED,
    UNAVAILABLE,
    UNKNOWN,
    HealthResult,
    run_quick_health_check,
    overall_health_status,
    health_summary,
)

from .failures import (
    ComponentFailureState,
    get_component_state,
    record_component_failure,
    record_component_success,
    list_component_states,
    clear_component_state,
    clear_all_component_states,
)

from .component_health import (
    run_component_health_checks,
)

from .diagnostic_state import (
    run_diagnostic_snapshot,
    format_diagnostic_snapshot,
)

from .performance import (
    PerformanceSummary,
    analyze_recent_performance,
    format_performance_report,
)

from .deep_diagnostics import (
    DeepDiagnosticResult,
    run_deep_diagnostic,
    format_deep_diagnostic_report,
)

from .self_awareness import (
    SelfAwarenessResult,
    get_self_awareness,
)

from .maintenance import (
    MaintenanceResult,
    list_maintenance_actions,
    run_maintenance_action,
)

from .ownership import (
    OwnershipRecord,
    get_ownership,
    find_ownership,
    list_ownership_records,
)

from .repair_scope import (
    RepairScope,
    build_repair_scope,
)

from .self_repair_bridge import (
    RepairRequest,
    RepairBridgeResult,
    build_repair_request,
    execute_repair_bridge,
)

from .backup import (
    BackupResult,
    IntegrityResult,
    create_backup,
    verify_backup,
    restore_backup,
    list_backups,
    prune_backups,
    validate_memory_database,
)

from .certification import (
    CERTIFIED,
    DEGRADED_CERTIFICATION,
    FAILED,
    CertificationCheck,
    CertificationResult,
    certification_to_dict,
    run_system_certification,
    format_certification_report,
)

from .diagnostics import (
    format_health_report,
)
