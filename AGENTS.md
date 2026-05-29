# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project Overview

`monarch-cli2` is an unofficial Typer/Rich command line interface for Monarch
Money. It uses `monarch-api2` for API access and exposes commands in the form:

```bash
monarch {group} {command} [flags...]
```

The CLI should stay organized by top-level feature group. Do not add nested
subcommand levels below group/command.

## Repository Layout

- `src/monarch_cli/app.py`: main Typer app and group registration
- `src/monarch_cli/groups/`: group-specific command modules
- `src/monarch_cli/output.py`: Rich table and JSON output helpers
- `src/monarch_cli/session.py`: session loading helpers
- `src/monarch_cli/options.py`: shared Typer option aliases
- `tests/groups/`: group-specific command tests
- `tests/test_output.py` and `tests/test_errors.py`: shared behavior tests

## Development Setup

This repo is usually developed with `monarch-api2` cloned next to it:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install httpx typer rich pytest
.venv/bin/python -m pip install -e ../monarch-api2
.venv/bin/python -m pip install --no-deps -e .
```

Run tests with:

```bash
.venv/bin/python -m pytest
```

Run the CLI locally with:

```bash
.venv/bin/monarch --help
```

## Command Design

- Keep the command shape flat: `monarch {group} {command}`.
- Keep user-facing text focused on the CLI behavior, not underlying API
  implementation details.
- Prefer clear command names over adding subgroups.
- Avoid boolean flag pairs such as `--foo/--no-foo`.
- For optional state changes, prefer value options such as `enabled|disabled`,
  `included|excluded`, or a single one-way flag such as `--include-hidden`.
- Preserve the existing soft blue/gray Rich/Typer visual style.
- Human output should be curated for readability.
- `--json` may expose a fuller structured object than the human table.
- `--json --raw` should include raw response data where available.

## Error Handling

- Use `@handle_cli_errors` on command functions.
- If the API returns a specific error message, surface it.
- If the API does not return a reason, do not guess one in the CLI.
- Destructive operations should use confirmation prompts unless a command has a
  `--yes` flag.

## Testing

- Add or update focused tests for any command behavior change.
- Group-specific command tests belong in `tests/groups/`.
- Shared formatting or error behavior tests belong at the top level of `tests/`.
- Prefer monkeypatching the imported API function in the command module rather
  than making live Monarch requests.
- Before finishing a change, run:

```bash
.venv/bin/python -m pytest
git diff --check
```

## Security And Privacy

- Never commit session files, tokens, receipts, exports, or personal financial
  data.
- Avoid adding tests that require live credentials or network calls.
- Be careful with examples: use fake ids, fake emails, and non-sensitive dates.

## Git Hygiene

- The working tree may contain user changes. Do not revert unrelated changes.
- Keep commits scoped to the requested work.
- Do not use destructive git commands unless the user explicitly asks for them.
