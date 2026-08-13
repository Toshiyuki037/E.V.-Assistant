from assistant.system.health import (
    HEALTHY, DEGRADED, UNAVAILABLE, UNKNOWN,
    HealthResult, health_result_to_dict, overall_health_status,
)

def test_health_result_serializes():
    result = HealthResult("memory.database", HEALTHY, "ok", {"x": 1})
    data = health_result_to_dict(result)
    assert data["component"] == "memory.database"
    assert data["status"] == HEALTHY
    assert data["metadata"]["x"] == 1

def test_overall_healthy():
    assert overall_health_status([
        HealthResult("a", HEALTHY),
        HealthResult("b", HEALTHY),
    ]) == HEALTHY

def test_overall_degraded():
    assert overall_health_status([
        HealthResult("a", HEALTHY),
        HealthResult("b", DEGRADED),
    ]) == DEGRADED

def test_unavailable_priority():
    assert overall_health_status([
        HealthResult("a", DEGRADED),
        HealthResult("b", UNAVAILABLE),
    ]) == UNAVAILABLE

def test_unknown_when_no_harder_failure():
    assert overall_health_status([
        HealthResult("a", HEALTHY),
        HealthResult("b", UNKNOWN),
    ]) == UNKNOWN
