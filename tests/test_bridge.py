"""Bridge tests against a fake `codex` executable (no network, no real login)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

BRIDGE = Path(__file__).resolve().parents[1] / "codex-delegate" / "scripts" / "codex_bridge.py"

FAKE_CODEX = r'''#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
with open(os.environ["FAKE_ARGV"], "a") as f:
    f.write(json.dumps(a) + "\n")
if a == ["--version"]:
    print("codex-cli 9.9.9"); sys.exit(0)
if a[:2] == ["login", "status"]:
    ok = os.path.exists(os.path.join(os.environ["CODEX_HOME"], "auth.json"))
    print("Logged in using ChatGPT" if ok else "Not logged in"); sys.exit(0 if ok else 1)
if a[0] == "exec":
    prompt = sys.stdin.read()
    out = a[a.index("-o") + 1]
    print(json.dumps({"type": "thread.started", "thread_id": "th-123"}))
    print(json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "rg foo"}}))
    print(json.dumps({"type": "item.completed",
                      "item": {"type": "file_change", "changes": [{"path": "a.py", "kind": "update"}]}}))
    print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}}))
    if os.environ.get("FAKE_FAIL"):
        sys.exit(7)
    with open(out, "w") as f:
        f.write("ANSWER preamble=%s" % prompt.startswith("You are working as a delegate"))
    sys.exit(0)
sys.exit(9)
'''

pytestmark = pytest.mark.skipif(os.name == "nt", reason="fake codex is a shebang script")


@pytest.fixture
def env(tmp_path, monkeypatch):
    fake = tmp_path / "codex"
    fake.write_text(FAKE_CODEX)
    fake.chmod(0o755)
    e = {k: v for k, v in os.environ.items() if not k.startswith(("CODEX_", "OPENAI_"))}
    e.update(CODEX_BIN=str(fake), CODEX_HOME=str(tmp_path / "home"),
             CODEX_BRIDGE_HOME=str(tmp_path / "bridge"), FAKE_ARGV=str(tmp_path / "argv.log"))
    return e


def bridge(env, *args, stdin=None, **extra):
    return subprocess.run([sys.executable, str(BRIDGE), *args], input=stdin, capture_output=True,
                          text=True, env={**env, **extra})


def calls(env):
    return [json.loads(line) for line in Path(env["FAKE_ARGV"]).read_text().splitlines()]


def receipt(stdout):
    line = next(l for l in stdout.splitlines() if l.startswith("--- codex receipt: "))
    return json.loads(line.split(": ", 1)[1])


def login(env):
    home = Path(env["CODEX_HOME"])
    home.mkdir(parents=True, exist_ok=True)
    (home / "auth.json").write_text("{}")


def test_status_reports_tiers_and_logged_out(env):
    r = bridge(env, "status", CODEX_MODEL_SOL="custom-sol")
    assert r.returncode == 1
    assert "auth: not logged in" in r.stdout
    assert "tier sol: custom-sol" in r.stdout and "tier luna: gpt-6-luna" in r.stdout


def test_setup_without_credentials_points_to_login(env):
    r = bridge(env, "setup")
    assert r.returncode == 1
    assert "codex_bridge.py login" in r.stdout


def test_setup_restores_auth_json_without_echoing_it(env):
    secret = "SECRET-REFRESH-TOKEN"
    r = bridge(env, "setup", CODEX_AUTH_JSON=json.dumps({"tokens": {"refresh_token": secret}}))
    assert r.returncode == 0, r.stderr
    auth = Path(env["CODEX_HOME"]) / "auth.json"
    assert json.loads(auth.read_text())["tokens"]["refresh_token"] == secret
    assert oct(auth.stat().st_mode & 0o777) == "0o600"
    assert secret not in r.stdout + r.stderr


def test_setup_rejects_invalid_auth_json(env):
    r = bridge(env, "setup", CODEX_AUTH_JSON="not json")
    assert r.returncode == 3
    assert not (Path(env["CODEX_HOME"]) / "auth.json").exists()


def test_run_refuses_when_logged_out(env):
    r = bridge(env, "run", "--prompt", "hi")
    assert r.returncode == 1
    assert "not logged in" in r.stderr
    assert not any(c[0] == "exec" for c in calls(env))


def test_run_builds_argv_and_prints_receipt(env, tmp_path):
    login(env)
    r = bridge(env, "run", "--tier", "sol", "--write", "--effort", "high", "--cd", str(tmp_path),
               stdin="find bugs", CODEX_MODEL_SOL="my-sol")
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("ANSWER preamble=True")
    argv = [c for c in calls(env) if c[0] == "exec"][-1]
    assert argv[argv.index("-m") + 1] == "my-sol"
    assert argv[argv.index("-s") + 1] == "workspace-write"
    assert argv[argv.index("-C") + 1] == str(tmp_path.resolve())
    assert 'model_reasoning_effort="high"' in argv and "--json" in argv and argv[-1] == "-"
    rec = receipt(r.stdout)
    assert rec["thread"] == "th-123" and rec["commands_run"] == 1
    assert rec["files_changed"] == ["update a.py"]
    assert Path(rec["log"]).exists()


def test_run_defaults_read_only_and_codex_model(env):
    login(env)
    r = bridge(env, "run", "--raw", "--prompt", "hi")
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("ANSWER preamble=False")
    argv = [c for c in calls(env) if c[0] == "exec"][-1]
    assert argv[argv.index("-s") + 1] == "read-only" and "-m" not in argv


def test_run_failure_returns_nonzero(env):
    login(env)
    r = bridge(env, "run", "--prompt", "hi", FAKE_FAIL="1")
    assert r.returncode == 7
    assert "codex failed (exit 7)" in r.stderr


def test_resume_targets_thread(env):
    login(env)
    r = bridge(env, "resume", "th-123", "--tier", "luna", "--prompt", "more")
    assert r.returncode == 0, r.stderr
    argv = [c for c in calls(env) if c[0] == "exec"][-1]
    assert argv[:2] == ["exec", "resume"] and argv[-2:] == ["th-123", "-"]
    assert argv[argv.index("-m") + 1] == "gpt-6-luna"
