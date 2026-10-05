# codex_bridge.py reference

`codex-delegate/scripts/codex_bridge.py` wraps the Codex CLI for Claude. It needs Python 3.9 or
later. It never prints or logs a credential.

```bash
python codex_bridge.py <command> [options]
```

## Commands

| Command | What it does |
|---|---|
| `setup` | Installs `@openai/codex` if no `codex` is found, then restores a login from the environment if one is set. |
| `login` | Runs `codex login --device-auth`. Prints a URL and a one-time code to approve in a browser. |
| `status` | Prints the `codex` path and version, the login state, and the model for each tier. |
| `run` | Sends one task to `codex exec`. Prints the final message, then the receipt. |
| `resume <thread>` | Sends a follow-up to the thread from an earlier receipt, through `codex exec resume`. |

### setup

| Option | Effect |
|---|---|
| `--allow-api-key` | If no ChatGPT login is set, log in with `OPENAI_API_KEY`. This bills the OpenAI API account, not the ChatGPT plan. |

`setup` looks for `codex` in this order: `CODEX_BIN`, `PATH`, then `~/.codex-bridge/npm`. If none
exists, it runs `npm install --prefix ~/.codex-bridge/npm @openai/codex`.

If `codex login status` fails, `setup` uses the first credential set in this list:

1. `CODEX_AUTH_JSON`, written to `$CODEX_HOME/auth.json` with mode `0600`.
2. `CODEX_ACCESS_TOKEN`, passed to `codex login --with-access-token`.
3. `OPENAI_API_KEY`, passed to `codex login --with-api-key`. Only with `--allow-api-key`.

### run and resume

`run` and `resume` both take these options.

| Option | Default | Effect |
|---|---|---|
| `--tier luna`, `--tier sol`, `--tier astra` | none | Model tier. Without `--tier` or `--model`, Codex uses its own configured model. |
| `--model <id>` | none | Exact model id. Overrides `--tier`. |
| `--effort <level>` | none | Passes `-c model_reasoning_effort="<level>"` to Codex. |
| `--prompt <text>` | none | Task text. |
| `--prompt-file <path>` | none | Reads the task from a file. Used if `--prompt` is not given. Without either, the task is read from stdin. |
| `--schema <path>` | none | JSON Schema the final message must match. |
| `--ephemeral` | off | Codex does not save the session. The thread can't be resumed. |
| `--timeout <seconds>` | `1800` | The bridge stops waiting after this many seconds. |

These options apply to `run` only.

| Option | Default | Effect |
|---|---|---|
| `--cd <dir>` | current directory | The working root Codex sees. |
| `--sandbox read-only`, `--sandbox workspace-write` | `read-only` | Codex sandbox mode. |
| `--write` | off | Same as `--sandbox workspace-write`. |
| `--add-dir <dir>` | none | Extra writable directory. Repeatable. Has an effect only with `workspace-write`. |
| `--raw` | off | Sends the task without the delegate preamble. |

Without `--raw`, `run` puts a short preamble before the task. The preamble tells Codex that
another agent will review its work, that it must not ask questions, and that it must end with a
complete final message. `resume` never adds the preamble.

Both commands refuse to start if `codex login status` fails.

## Receipt

After the final message, `run` and `resume` print one line that starts with
`--- codex receipt: ` and ends with a JSON object.

| Field | Meaning |
|---|---|
| `exit` | Exit code of `codex exec`. |
| `thread` | Codex thread id. Pass it to `resume`. |
| `model` | Model that Codex recorded for the turn. `null` if Codex saved no session. |
| `seconds` | Wall-clock time of the call. |
| `usage` | Token usage from Codex's `turn.completed` event. |
| `commands_run` | Number of shell commands Codex ran. |
| `files_changed` | Each file Codex changed, as `<kind> <path>`. |
| `errors` | Messages from `error` and `turn.failed` events. |
| `log` | Path of the full event log for this call. |

## Exit codes

| Command | Code | Meaning |
|---|---|---|
| `setup` | `0` | Codex is installed and logged in. |
| `setup` | `1` | No login and no credential in the environment. Run `login`. |
| `setup` | `2` | npm is missing, or the install failed. |
| `setup` | `3` | A credential was set but the login failed, or `CODEX_AUTH_JSON` is not valid JSON. |
| `status` | `0` | Logged in. |
| `status` | `1` | Not installed or not logged in. |
| `run`, `resume` | `0` | Codex finished and returned a final message. |
| `run`, `resume` | `1` | `codex` not found, not logged in, empty task, or no final message. |
| `run`, `resume` | `124` | Timed out. |
| `run`, `resume` | other | Exit code of `codex exec`. |
| `login` | any | Exit code of `codex login --device-auth`. |

## Environment variables

| Variable | Default | Used for |
|---|---|---|
| `CODEX_MODEL_LUNA` | `gpt-6-luna` | Model for `--tier luna`. |
| `CODEX_MODEL_SOL` | `gpt-6.1-sol` | Model for `--tier sol`. |
| `CODEX_MODEL_ASTRA` | `gpt-6-astra` | Model for `--tier astra`. |
| `CODEX_AUTH_JSON` | none | Contents of a ChatGPT `auth.json`, restored by `setup`. |
| `CODEX_ACCESS_TOKEN` | none | Access token for `setup` to log in with. |
| `OPENAI_API_KEY` | none | API key for `setup --allow-api-key`. |
| `CODEX_BIN` | none | Path or name of the `codex` executable. |
| `CODEX_HOME` | `~/.codex` | Codex's own home. Holds `auth.json` and saved sessions. |
| `CODEX_BRIDGE_HOME` | `~/.codex-bridge` | Holds the bridge's npm install (`npm/`) and call logs (`logs/`). |

## Repository layout

| Path | Contents |
|---|---|
| `codex-delegate/SKILL.md` | Instructions Claude follows: when to delegate, how to route to Luna and Sol, how to review the answer. |
| `codex-delegate/scripts/codex_bridge.py` | The wrapper this page describes. |
| `tests/test_bridge.py` | Tests against a fake `codex` executable. No network, no login. |
| `package.py` | Builds `dist/codex-delegate.zip`. |
| `.github/workflows/tests.yml` | Runs the tests on Linux and macOS, then uploads the zip. |
