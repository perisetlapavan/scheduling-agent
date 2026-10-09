import json
import sys


def load(label):
    with open(f"results_{label}.json", encoding="utf-8") as f:
        data = json.load(f)
    # {scenario_id: pass_count}
    scores = {s["id"]: s["pass_count"] for s in data["scenarios"]}
    return scores, data["repeats"]


def compare(before_label="before", after_label="after"):
    before, repeats = load(before_label)
    after, _ = load(after_label)

    improved = []
    regressed = []

    print(f"{'scenario':32} {'before':>7} {'after':>7}")
    print("-" * 50)
    for scenario_id in before:
        b = before[scenario_id]
        a = after.get(scenario_id, 0)
        if a > b:
            note = "  IMPROVED"
            improved.append(scenario_id)
        elif a < b:
            note = "  REGRESSED"
            regressed.append(scenario_id)
        else:
            note = ""
        print(f"{scenario_id:32} {b}/{repeats:>5} {a}/{repeats:>5}{note}")

    total_b = sum(before.values())
    total_a = sum(after.values())
    total_runs = repeats * len(before)
    print("-" * 50)
    print(f"{'TOTAL':32} {total_b}/{total_runs:>3} {total_a}/{total_runs:>3}")
    print()
    print("Improved: ", improved if improved else "none")
    print("Regressed:", regressed if regressed else "none")


if __name__ == "__main__":
    # usage: python compare.py before after
    before_label = sys.argv[1] if len(sys.argv) > 1 else "before"
    after_label = sys.argv[2] if len(sys.argv) > 2 else "after"
    compare(before_label, after_label)