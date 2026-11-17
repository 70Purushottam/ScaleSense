import json, pathlib, pytest
from app.schema import Graph
from app import simulate

BENCH = pathlib.Path(__file__).parents[2] / "examples" / "benchmark" / "b03_clean.json"


def clean():
    return Graph(**json.loads(BENCH.read_text())["graph"])


def test_losing_one_api_replica_overloads_api():
    r = simulate.failure_report(clean(), {"api": 1})
    assert "api" in r["newly_overloaded"] and r["service_available"]


def test_killing_cache_cuts_database():
    r = simulate.failure_report(clean(), {"cache": None})
    assert r["data_stores_lost"] == ["db"] and not r["service_available"]


def test_cannot_fail_client_or_unknown():
    with pytest.raises(ValueError):
        simulate.apply_failure(clean(), {"u": None})
    with pytest.raises(ValueError):
        simulate.apply_failure(clean(), {"ghost": None})


def test_ramp_finds_api_bottleneck():
    r = simulate.ramp(clean())
    assert r["bottleneck"] == "api"
    assert r["max_sustainable_qps"] == pytest.approx(1500, rel=1e-3)