from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "plugins" / "amanerp-second-opinion" / "scripts" / "second_opinion.py"

REQUIRED_FLAGS = [
    "--print",
    "--safe-mode",
    "--tools",
    "--no-chrome",
    "--no-session-persistence",
    "--name",
    "--output-format",
    "--verbose",
    "--json-schema",
    "--max-turns",
    "--max-budget-usd",
    "--model",
    "--effort",
]

REQUIRED_HELP_FLAGS = [flag for flag in REQUIRED_FLAGS if flag != "--max-turns"]

ADVISORY_RESULT: dict[str, Any] = {
    "status": "completed",
    "executive_summary": "Choose the bounded option after validating the rollback path.",
    "facts": [
        {
            "claim": "The supplied constraint requires reversibility.",
            "evidence": ["question"],
        }
    ],
    "assumptions": ["The deployment window is fixed."],
    "options": [
        {
            "name": "Option A",
            "benefits": ["Reversible"],
            "drawbacks": ["More setup"],
            "risks": ["Operator error"],
        }
    ],
    "material_risks": ["Rollback has not been rehearsed."],
    "recommendation": {
        "choice": "Option A",
        "rationale": "It meets the stated safety constraint.",
        "confidence": "high",
        "conditions_that_change_it": ["Rollback proves unavailable."],
    },
    "open_questions": ["Has rollback been rehearsed?"],
    "validation_steps": ["Run the rollback rehearsal."],
}

PR_RESULT: dict[str, Any] = {
    "verdict": "request_changes",
    "confidence": "high",
    "summary": "One correctness issue should be fixed before merge.",
    "findings": [
        {
            "id": "F-1",
            "severity": "high",
            "confidence": "high",
            "category": "correctness",
            "file": "src/example.py",
            "line": 2,
            "title": "Incorrect fallback",
            "evidence": "The added branch returns success on failure.",
            "failure_scenario": "A failed operation is reported as successful.",
            "impact": "Callers persist incorrect state.",
            "recommended_fix": "Return the original error and add a failure-path test.",
        }
    ],
    "residual_risks": ["No live integration evidence was supplied."],
    "verification_gaps": ["Integration tests were not included."],
}


FAKE_CLAUDE = (
    r"""#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

args = sys.argv[1:]
control = json.loads(
    (Path(sys.argv[0]).resolve().parent / ".second-opinion-test-control.json").read_text(
        encoding="utf-8"
    )
)
log = control.get("FAKE_CLAUDE_LOG")
if log:
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "args": args,
            "env": {
                "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
                "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN"),
                "ANTHROPIC_BASE_URL": os.environ.get("ANTHROPIC_BASE_URL"),
                "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": os.environ.get(
                    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"
                ),
                "CLAUDE_CONFIG_DIR": os.environ.get("CLAUDE_CONFIG_DIR"),
                "CLAUDE_CODE_USE_BEDROCK": os.environ.get("CLAUDE_CODE_USE_BEDROCK"),
            },
        }) + "\n")

if args == ["--version"]:
    forced_stdout = int(control.get("FAKE_CLAUDE_PROBE_STDOUT_BYTES", "0"))
    if forced_stdout:
        sys.stdout.write("x" * forced_stdout)
        raise SystemExit(0)
    print(control.get("FAKE_CLAUDE_VERSION", "2.1.210 (Claude Code)"))
    raise SystemExit(0)

if args == ["--help"]:
    missing = control.get("FAKE_CLAUDE_MISSING_FLAG", "")
    flags = """
    + repr(" ".join(REQUIRED_HELP_FLAGS))
    + r""".split()
    print("\n".join(flag for flag in flags if flag != missing))
    raise SystemExit(0)

if args == ["--max-turns", "1", "--version"]:
    if control.get("FAKE_CLAUDE_MAX_TURNS", "present") != "present":
        print("error: unknown option '--max-turns'", file=sys.stderr)
        raise SystemExit(1)
    print(control.get("FAKE_CLAUDE_VERSION", "2.1.210 (Claude Code)"))
    raise SystemExit(0)

if args == ["auth", "status", "--json"]:
    if control.get("FAKE_CLAUDE_AUTH", "ok") != "ok":
        print(json.dumps({"loggedIn": False, "email": "private@example.invalid"}))
        raise SystemExit(1)
    print(json.dumps({
        "loggedIn": True,
        "authMethod": "claude.ai",
        "apiProvider": "firstParty",
        "subscriptionType": "max",
        "email": "private@example.invalid",
        "orgId": "secret-org-id",
    }))
    raise SystemExit(0)

mode = control.get("FAKE_CLAUDE_MODE", "success")
_ = sys.stdin.read()
forced_stdout = int(control.get("FAKE_CLAUDE_STDOUT_BYTES", "0"))
if forced_stdout:
    sys.stdout.write("x" * forced_stdout)
    raise SystemExit(0)
if mode == "timeout":
    time.sleep(10)
if mode == "malformed":
    print("not-json")
    raise SystemExit(0)

result = json.loads(control["FAKE_CLAUDE_RESULT"])
if mode == "invalid-enum":
    result["status"] = "invented"
if mode == "extra-property":
    result["unexpected"] = "must fail"
if mode == "negative-line":
    result["findings"][0]["line"] = -1
requested_model = args[args.index("--model") + 1]
primary_model = control.get(
    "FAKE_CLAUDE_PRIMARY_MODEL",
    "claude-opus-4-8" if requested_model == "opus" else "claude-sonnet-4-6",
)
session_id = "00000000-0000-4000-8000-000000000001"
if mode != "missing-init":
    print(json.dumps({
        "type": "system",
        "subtype": "init",
        "session_id": session_id,
        "model": primary_model,
        "claude_code_version": control.get(
            "FAKE_CLAUDE_VERSION", "2.1.210 (Claude Code)"
        ).split()[0],
    }))
if mode != "missing-assistant":
    print(json.dumps({
        "type": "assistant",
        "session_id": session_id,
        "message": {
            "model": primary_model,
            "type": "message",
            "role": "assistant",
            "content": [],
        },
    }))
if mode == "error":
    print(json.dumps({
        "type": "result",
        "subtype": "error_during_execution",
        "is_error": True,
        "session_id": session_id,
        "result": "provider token=very-secret-value failed",
        "modelUsage": {primary_model: {"inputTokens": 4, "outputTokens": 1}},
    }))
    print("token=very-secret-value", file=sys.stderr)
    raise SystemExit(23)
model_usage = {
    primary_model: {
        "inputTokens": 10,
        "outputTokens": 20,
        "cacheReadInputTokens": 5,
        "cacheCreationInputTokens": 3,
        "costUSD": 0.01,
    }
}
auxiliary_model = control.get("FAKE_CLAUDE_AUX_MODEL")
if auxiliary_model:
    model_usage[auxiliary_model] = {
        "inputTokens": 10,
        "outputTokens": 2,
        "cacheReadInputTokens": 0,
        "cacheCreationInputTokens": 0,
        "costUSD": 0.001,
    }
if mode == "invalid-model-usage":
    model_usage[primary_model]["costUSD"] = "0.01"
envelope = {
    "type": "result",
    "subtype": "success",
    "is_error": False,
    "duration_ms": 12,
    "duration_api_ms": 10,
    "num_turns": 2,
    "total_cost_usd": 0.01,
    "session_id": "00000000-0000-4000-8000-000000000001",
    "structured_output": result,
    "modelUsage": model_usage,
}
if mode == "no-structured-output":
    envelope.pop("structured_output")
if mode == "turn-breach":
    envelope["num_turns"] = 99
if mode == "cost-breach":
    envelope["total_cost_usd"] = 99.0
if mode == "missing-turn-usage":
    envelope.pop("num_turns")
if mode == "string-cost-usage":
    envelope["total_cost_usd"] = "0.01"
if mode != "missing-result":
    print(json.dumps(envelope))
"""
)


FAKE_GH = r"""#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
control = json.loads(
    (Path(sys.argv[0]).resolve().parent / ".second-opinion-test-control.json").read_text(
        encoding="utf-8"
    )
)
log = control.get("FAKE_GH_LOG")
prior = []
if log and os.path.exists(log):
    with open(log, encoding="utf-8") as handle:
        prior = [json.loads(line) for line in handle if line.strip()]
if log:
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "args": args,
            "env": {
                "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
                "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN"),
            },
        }) + "\n")

if args == ["--version"]:
    print("gh version 2.92.0 (fake)")
    raise SystemExit(0)
if args == ["auth", "status"]:
    raise SystemExit(0 if control.get("FAKE_GH_AUTH", "ok") == "ok" else 1)
if args[:2] == ["pr", "diff"]:
    forced_size = int(control.get("FAKE_GH_DIFF_BYTES", "0"))
    if forced_size:
        sys.stdout.write("x" * forced_size)
        raise SystemExit(0)
    print("diff --git a/src/example.py b/src/example.py")
    print("--- a/src/example.py")
    print("+++ b/src/example.py")
    print("@@ -1 +1,2 @@")
    print(" value = 1")
    print("+value = 2")
    raise SystemExit(0)
if args[:2] == ["pr", "view"]:
    view_count = sum(1 for item in prior if item["args"][:2] == ["pr", "view"])
    heads = control.get("FAKE_GH_HEADS", "head-a,head-a").split(",")
    bases = control.get("FAKE_GH_BASES", "base-a,base-a").split(",")
    head = heads[min(view_count, len(heads) - 1)]
    base = bases[min(view_count, len(bases) - 1)]
    print(json.dumps({
        "number": 42,
        "title": "Improve behavior",
        "url": "https://github.com/example/project/pull/42",
        "author": {"login": "reviewer"},
        "baseRefName": "main",
        "headRefName": "feature",
        "baseRefOid": base,
        "headRefOid": head,
        "additions": 1,
        "deletions": 0,
        "changedFiles": 1,
    }))
    raise SystemExit(0)
print("unexpected gh invocation", file=sys.stderr)
raise SystemExit(2)
"""


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def fake_environment(
    temp: Path, result: dict[str, Any] | None = None
) -> tuple[dict[str, str], Path, Path]:
    bin_dir = temp / "bin"
    bin_dir.mkdir()
    claude = bin_dir / "claude"
    gh = bin_dir / "gh"
    write_executable(claude, FAKE_CLAUDE)
    write_executable(gh, FAKE_GH)
    claude_log = temp / "claude.jsonl"
    gh_log = temp / "gh.jsonl"
    env = os.environ.copy()
    env.update(
        {
            "AMANERP_SECOND_OPINION_CLAUDE_BIN": str(claude),
            "AMANERP_SECOND_OPINION_GH_BIN": str(gh),
            "FAKE_CLAUDE_LOG": str(claude_log),
            "FAKE_GH_LOG": str(gh_log),
            "FAKE_CLAUDE_RESULT": json.dumps(result or ADVISORY_RESULT),
            "ANTHROPIC_API_KEY": "preserve-this-auth-value",
            "GITHUB_TOKEN": "preserve-this-github-value",
            "ANTHROPIC_BASE_URL": "https://must-not-reach-child.invalid",
            "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "must-not-reach-child",
            "CLAUDE_CONFIG_DIR": "/must/not/reach/child",
            "CLAUDE_CODE_USE_BEDROCK": "must-not-reach-child",
        }
    )
    return env, claude_log, gh_log


def run_cli(
    args: list[str], *, cwd: Path, env: dict[str, str], timeout: float = 10
) -> subprocess.CompletedProcess[str]:
    control = {name: value for name, value in env.items() if name.startswith("FAKE_")}
    control_path = (
        Path(env["AMANERP_SECOND_OPINION_CLAUDE_BIN"]).parent
        / ".second-opinion-test-control.json"
    )
    control_path.write_text(json.dumps(control), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def stdout_json(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return json.loads(completed.stdout)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
