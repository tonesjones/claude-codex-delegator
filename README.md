# codex-delegate

A Claude skill that lets Claude hand tasks to the Codex CLI on your ChatGPT/Codex subscription,
in any project, locally or in Claude Code cloud sessions.

## 1. Install the skill (once, applies everywhere)

Build the zip with `python package.py` (writes `dist/codex-delegate.zip`), or download the
`codex-delegate-skill` artifact from the latest CI run. Upload it in the Skills section of your
claude.ai settings. Account skills
sync into the desktop app, Claude Code locally, and cloud sessions, so it is not tied to any
repository.

For Claude Code locally only, you can instead copy the `codex-delegate/` folder into
`~/.claude/skills/`.

## 2. Local machine

Nothing more if `codex` is already installed and you have run `codex login` once. Otherwise
Claude runs `setup` (installs the CLI with npm) and `login`.

## 3. Cloud sessions

Cloud containers start empty each session, so Codex needs a login each time. Pick one option:

**A. Device-code login per session (no stored secret).** Claude runs the login, shows you a URL
and a code, and you approve it in your browser. This takes about 20 seconds per session. If
ChatGPT says device-code login is disabled, turn it on in your ChatGPT security settings.

**B. Stored login (no prompt each session).** In the cloud environment's settings, add an
environment variable `CODEX_AUTH_JSON` whose value is the full contents of your local
`~/.codex/auth.json` (on Windows `%USERPROFILE%\.codex\auth.json`). Treat it like a password:
anyone who can use that environment can spend your subscription. If Codex later refreshes the
token and the stored copy stops working, copy the file again.

Whichever you pick, also check in the environment settings:

- **Network access**: allow `chatgpt.com`, `auth.openai.com` and `api.openai.com` (plus the
  default package-manager list, so npm can install the CLI).
- **Setup script** (optional, makes sessions start ready): `npm install -g @openai/codex`

## 4. Model names

The tiers default to `gpt-6-luna`, `gpt-6-sol` and `gpt-6-astra`. To change them without
editing the skill, set `CODEX_MODEL_LUNA`, `CODEX_MODEL_SOL` and `CODEX_MODEL_ASTRA`.

## Use

Ask Claude something like "use Codex to triage these 40 lint findings" or "get a Sol second
opinion on this auth change". Claude picks the tier, runs the task, checks every cited line, and
reports what it kept and what it rejected.

## Repository layout

| Path | What it is |
|---|---|
| `codex-delegate/SKILL.md` | Instructions Claude follows: when to delegate, Luna/Sol routing, review rules |
| `codex-delegate/scripts/codex_bridge.py` | The CLI wrapper: `setup`, `login`, `status`, `run`, `resume` |
| `tests/` | Tests against a fake `codex` executable (no network, no login) |
| `package.py` | Builds the uploadable zip |

After changing the skill, run `python -m pytest`, rebuild the zip, and upload it again.
