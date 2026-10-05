---
name: codex-delegate
description: Delegate bounded work to OpenAI Codex (the person's ChatGPT/Codex subscription) through the Codex CLI, with Claude as orchestrator and final reviewer. Routes each task to GPT-6 Luna (bulk, mechanical) or Sol (security-sensitive, judgment), runs tasks in parallel, and verifies every answer before using it. Use when asked to "use Codex", "ask Codex", "route to Luna/Sol", "get a second opinion from GPT", or to fan out bulk reading, triage, test writing, or review across many files. Works in local and cloud sessions.
---

# Codex delegate

You orchestrate; Codex does delegated work; you own the result. Everything goes through
`scripts/codex_bridge.py` in this skill's directory (call it `$BRIDGE` below; run it with
`python3`, or `python` on Windows).

## 1. Make sure Codex is ready (once per session)

```bash
python3 $BRIDGE status          # installed? logged in? which model each tier maps to
python3 $BRIDGE setup           # installs @openai/codex if missing; restores login from CODEX_AUTH_JSON / CODEX_ACCESS_TOKEN
```

If setup reports "not logged in", run `python3 $BRIDGE login` **in the background**, read its
output for the verification URL and one-time code, and give both to the person to approve in
their browser. Wait for the command to exit, then run `status` again. Never ask the person to
paste a token or `auth.json` into the chat. Never print, cat, or log `~/.codex/auth.json` or any
`CODEX_*`/`OPENAI_*` secret. Use `--allow-api-key` only if the person asks for API billing.

If OpenAI hosts are blocked (network errors to chatgpt.com, auth.openai.com, or api.openai.com),
tell the person which host failed. In a cloud session they allow it under the environment's
network settings.

## 2. Decide whether to delegate

Delegate when the task is self-contained and its result is cheap to check: bulk reading or
summarizing, triage across many files, first-draft tests, mechanical refactors in an isolated
tree, an independent second opinion on a diff or a finding.

Keep it yourself when it is small, when the context needed is mostly already in your
conversation, when it needs tools only you have (connectors, MCP, GitHub), or when it touches
secrets. Never send credentials, `.env` files, tokens, or data the project marks as private or
not-for-models. Follow the project's own rules first: if a repo has its own model pipeline (for
example the finding-validation-agent's `fva assess`), use that instead of this bridge for its data.

## 3. Route

| Tier | Use for |
|---|---|
| `--tier luna` | clear, bounded, low-ambiguity work: summaries, inventories, boilerplate, dead-code and lint-style checks, first-pass triage |
| `--tier sol` | security-sensitive or judgment-heavy work: injection, authn/authz, crypto, SSRF, concurrency, design review, anything critical-severity, any task where a wrong answer is costly |
| `--tier astra` | only when the person names it |

Escalate once: if a Luna answer is vague, contradicts the code, or misses the requested format,
rerun that task on Sol. Don't retry beyond that; do it yourself or report the gap.
`--effort low|medium|high` tunes reasoning depth within a tier.

## 4. Write the task

Codex starts cold. Each prompt must stand alone: the goal, exact file paths or globs, what
"done" means, the output format, and the constraints (read-only, no network, which files are
off-limits). Ask for file:line citations for every claim. For machine-readable results, write a
JSON Schema file and pass `--schema`.

## 5. Run

```bash
# read-only (default): Codex can read files under --cd and run read-only commands
python3 $BRIDGE run --tier luna --cd <repo> --prompt-file task.md

# writes: only into a scratch git worktree, never your working tree
git worktree add ../wt-codex-<task> -b codex/<task>
python3 $BRIDGE run --tier sol --write --cd ../wt-codex-<task> --prompt-file task.md

# follow-up on the same Codex thread (thread id comes from the receipt)
python3 $BRIDGE resume <thread> --prompt "Now add tests for the two cases you found."
```

Stdout is Codex's final message, then a single `--- codex receipt:` JSON line with `exit`,
`thread`, `model`, `usage`, `commands_run`, `files_changed`, `errors`, and the `log` path.

- Tasks over a minute or two: run with Bash `run_in_background` and keep working; you are
  notified when they finish. Independent tasks can run in parallel (keep it to about 4 at once).
- The default timeout is 1800 s (`--timeout`).
- `--ephemeral` skips saving the Codex session, which also disables `resume`.

## 6. Review (always)

Codex output is a draft from a junior colleague, not a fact.

- Open every cited file:line and confirm the claim before repeating it. Drop what doesn't hold.
- For write runs, read `git -C <worktree> diff` in full, run the project's tests and linters in
  the worktree, then merge or cherry-pick only what you have verified. Remove the worktree when
  done.
- Check the receipt: a `model` different from the tier requested, non-empty `errors`, or
  unexpected `files_changed` means stop and look at the log.
- Tell the person what was delegated, to which tier, what you kept, and what you rejected.
