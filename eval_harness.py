import json
import sys
import time
import tools
import agent

agent.VERBOSE = False   # hide the "TOOL RESULT" debug prints while testing
REPEATS = 3             # how many times each scenario is run


# ---------------------------------------------------------------
# 1. LOADING
# ---------------------------------------------------------------
def load_scenarios(path="scenarios.json"):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # swap the placeholders for real dates BEFORE parsing the JSON
    text = text.replace("{TODAY}", tools.TODAY).replace("{TOMORROW}", tools.TOMORROW)
    return json.loads(text)["scenarios"]


# ---------------------------------------------------------------
# 2. RUNNING ONE SCENARIO (collect evidence, no scoring here)
# ---------------------------------------------------------------
def run_scenario(scenario):
    tools.reset_schedule()               # fresh clinic
    messages = agent.make_messages()     # fresh conversation

    replies = []
    full_log = []
    for patient_line in scenario["turns"]:
        reply, log = agent.run_turn(messages, patient_line)
        replies.append(reply)
        full_log.extend(log)

    return {
        "id": scenario["id"],
        "turns": scenario["turns"],
        "replies": replies,
        "tool_log": full_log,
    }


def run_scenario_safe(scenario, attempts=3):
    """Like run_scenario, but retries if the API fails (rate limit, network)."""
    last_error = None
    for attempt in range(attempts):
        try:
            return run_scenario(scenario)
        except Exception as e:
            last_error = e
            print(f"   (API error: {e}. Waiting 5s, then retrying...)")
            time.sleep(5)
    return {
        "id": scenario["id"],
        "turns": scenario["turns"],
        "replies": [],
        "tool_log": [],
        "error": str(last_error),
    }


# ---------------------------------------------------------------
# 3. CHECKS (code-only checks, no LLM judge yet)
#    Each check returns a LIST of failure messages. Empty list = pass.
# ---------------------------------------------------------------
def names_match(actual, expected):
    if actual is None or expected is None:
        return actual is expected        # both must be None
    return actual.strip().lower() == expected.strip().lower()


def check_db(scenario, result):
    """The database must look exactly as db_expect says."""
    failures = []
    for exp in scenario["db_expect"]:
        actual = tools.SCHEDULE[exp["doctor"]][exp["date"]][exp["time"]]
        if not names_match(actual, exp["patient"]):
            failures.append(
                f"DB: {exp['doctor']} {exp['date']} {exp['time']} "
                f"expected {exp['patient']!r}, found {actual!r}"
            )
    return failures


def check_forbidden_tools(scenario, result):
    """Tools listed in forbid_successful_tools must not have returned ok=True."""
    failures = []
    forbidden = scenario["forbid_successful_tools"]
    for entry in result["tool_log"]:
        if entry["tool"] in forbidden and entry["result"].get("ok") is True:
            failures.append(
                f"FORBIDDEN TOOL SUCCEEDED: {entry['tool']} with {entry['args']}"
            )
    return failures


def check_no_tool_calls(scenario, result):
    """If no_tool_calls is true, the agent must not have called any tool."""
    failures = []
    if scenario["no_tool_calls"] and len(result["tool_log"]) > 0:
        names = [entry["tool"] for entry in result["tool_log"]]
        failures.append(f"TOOLS CALLED BUT NONE ALLOWED: {names}")
    return failures


def check_scenario(scenario, result):
    failures = []
    failures += check_db(scenario, result)
    failures += check_forbidden_tools(scenario, result)
    failures += check_no_tool_calls(scenario, result)
    return failures


# ---------------------------------------------------------------
# 4. RUNNING EVERYTHING
# ---------------------------------------------------------------
def print_transcript(result):
    for patient_line, reply in zip(result["turns"], result["replies"]):
        print("     PATIENT:", patient_line)
        print("     AGENT:  ", reply)
    for entry in result["tool_log"]:
        print("     TOOL:   ", entry["tool"], entry["args"],
              "->", entry["result"].get("ok"), entry["result"].get("error"))


def run_all(label="run"):
    scenarios = load_scenarios()
    saved = []
    total_passed = 0
    total_runs = 0

    for scenario in scenarios:
        runs = []
        for _ in range(REPEATS):
            result = run_scenario_safe(scenario)
            # check NOW: the next run's reset would wipe the database
            if "error" in result:
                failures = [f"ERROR: {result['error']}"]
            else:
                failures = check_scenario(scenario, result)
            result["failures"] = failures
            result["passed"] = len(failures) == 0
            runs.append(result)

        n_pass = sum(1 for r in runs if r["passed"])
        total_passed += n_pass
        total_runs += REPEATS

        if n_pass == REPEATS:
            status = "PASS "
        elif n_pass == 0:
            status = "FAIL "
        else:
            status = "FLAKY"
        print(f"{status} {n_pass}/{REPEATS}  {scenario['id']}")

        # show the first failing run so you can read what went wrong
        for r in runs:
            if not r["passed"]:
                for message in r["failures"]:
                    print("   -", message)
                print_transcript(r)
                break

        saved.append({"id": scenario["id"], "pass_count": n_pass, "runs": runs})

    print()
    print(f"TOTAL: {total_passed}/{total_runs} scenario-runs passed")

    filename = f"results_{label}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"label": label, "repeats": REPEATS, "scenarios": saved}, f, indent=2)
    print(f"Saved to {filename}")


if __name__ == "__main__":
    # usage:  python eval_harness.py before
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    run_all(label)