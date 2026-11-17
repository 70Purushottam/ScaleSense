"""Score the rule engine on the seeded-flaw benchmark. Run: python scripts/evaluate.py"""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.schema import Graph
from app import rules

WHOLE_GRAPH = {"long_sync_chain", "cycle"}


def key(f):
    return f["rule"] if f["rule"] in WHOLE_GRAPH else f"{f['rule']}:{f['nodes'][0]}"


tp = fp = fn = 0
clean_total = clean_alarms = 0
for path in sorted((ROOT / "examples" / "benchmark").glob("*.json")):
    case = json.loads(path.read_text())
    got = {key(f) for f in rules.run_all(Graph(**case["graph"]))}
    exp = set(case["expected_findings"])
    tp += len(got & exp); fp += len(got - exp); fn += len(exp - got)
    if not exp:
        clean_total += 1; clean_alarms += bool(got)
    status = "OK " if got == exp else "DIFF"
    print(f"{status} {path.stem}: missed={sorted(exp - got)} extra={sorted(got - exp)}")

prec = tp / (tp + fp) if tp + fp else 1.0
rec = tp / (tp + fn) if tp + fn else 1.0
print(f"\nprecision={prec:.2f} recall={rec:.2f} tp={tp} fp={fp} fn={fn}")
print(f"false alarms on clean designs: {clean_alarms}/{clean_total}")