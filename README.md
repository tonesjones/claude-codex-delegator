# codex-delegate

codex-delegate is a Claude skill that lets Claude send tasks to the Codex CLI and bill them to
your ChatGPT plan instead of an API account. Claude stays in charge. It decides what to send,
picks the model, and checks every file and line Codex cites before it uses the answer.

The skill works in any project, in Claude Code on your machine and in Claude Code cloud sessions.

## Install the skill

1. Build the zip:

   ```bash
   python package.py
   ```

   The script writes `dist/codex-delegate.zip`. You can also download the `codex-delegate-skill`
   artifact from the latest CI run.
2. Upload the zip in the Skills section of your claude.ai settings.

claude.ai syncs account skills into cloud sessions, so one upload covers every project. If the
skill doesn't show up in Claude Code on your machine, copy the `codex-delegate/` folder into
`~/.claude/skills/`.

## Set up Codex on your machine

If you already use Codex and have run `codex login`, there is nothing to do.

If you haven't, Claude handles it the first time you ask for Codex. It runs
`codex_bridge.py setup` to install the CLI with npm, then `codex_bridge.py login`, which prints a
URL and a code for you to approve in your browser. You need Python 3.9 or later, Node.js, and npm.

## Set up a cloud environment

Each cloud session starts in a new container with no Codex login. Choose how Codex logs in, then
allow the OpenAI hosts.

### Choose how Codex logs in

Start with the device code. Switch to a stored login if approving a code every session gets old.

- **Device code each session.** Claude runs the login and gives you a URL and a code to approve
  in your browser. It takes about 20 seconds, and the environment stores nothing. If ChatGPT
  says device-code login is off, turn it on in your ChatGPT security settings.
- **Stored login.** In the environment's settings, add the variable `CODEX_AUTH_JSON` and set it
  to the full contents of `~/.codex/auth.json` from your machine. On Windows, the file is
  `%USERPROFILE%\.codex\auth.json`. Anyone who can start a session in that environment can spend
  your plan, so treat the value like a password. If Codex refreshes the token and the stored
  copy stops working, copy the file again.

### Allow the OpenAI hosts

In the environment's network settings, allow these hosts. Keep the default package-manager list
too, because npm needs it to install the CLI.

- `chatgpt.com`
- `auth.openai.com`
- `api.openai.com`

### Install Codex in the setup script (optional)

To start each session with Codex already installed, add this line to the environment's setup
script:

```bash
npm install -g @openai/codex
```

## Ask Claude to use Codex

Ask in plain words. For example:

- "Use Codex to triage these 40 lint findings."
- "Get a Sol second opinion on this auth change."

Claude sends bounded, mechanical work to Luna and security-sensitive or judgment-heavy work to
Sol. It uses Astra only when you name it. Codex runs read-only unless the task has to write
files, and then it writes only in a separate git worktree. When the answer comes back, Claude
checks each claim against the code and tells you what it kept and what it threw out.

## Change the model names

The tiers map to `gpt-6-luna`, `gpt-6.1-sol`, and `gpt-6-astra`. To use other models, set
`CODEX_MODEL_LUNA`, `CODEX_MODEL_SOL`, or `CODEX_MODEL_ASTRA` in the environment. You don't need
to edit the skill.

## Change the skill

1. Edit the files in `codex-delegate/`.
2. Run the tests:

   ```bash
   python -m pytest
   ```

   The tests use a fake `codex`, so they need no network and no login. They skip on Windows. CI
   runs them on Linux and macOS.
3. Rebuild the zip with `python package.py` and upload it again.

For commands, flags, environment variables, exit codes, and the repository layout, see the
[codex_bridge.py reference](docs/reference.md).
