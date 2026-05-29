# monarch-cli2

Unofficial command line interface for Monarch Money.

This project is not affiliated with, endorsed by, or supported by Monarch Money.

`monarch-cli2` wraps the public command surface from
[`monarch-api2`](https://github.com/erikrubstein/monarch-api2) into a Typer/Rich
CLI organized by Monarch feature area:

```bash
monarch {group} {command} [flags...]
```

## Features

- Authentication helpers for login, status, export, and logout
- Human-friendly Rich tables for day-to-day use
- `--json` output for scripts and automation
- `--raw` JSON output when you need the underlying response data
- Flat group/command structure matching the main Monarch feature areas
- Commands for accounts, transactions, receipts, cashflow, reports, merchants,
  tags, household, categories, recurring items, investments, goals, and budgets

## Installation

This package depends on `monarch-api2`, which is currently installed directly
from GitHub.

```bash
pipx install git+https://github.com/erikrubstein/monarch-cli2.git
```

After installation, the `monarch` command should be available on your `PATH`:

```bash
monarch --help
```

## Usage

Start by signing in:

```bash
monarch auth login you@example.com
monarch auth status
```

By default, the CLI saves a session file under your user config directory. You
can pass `--session-path` to use a different session file.

Common commands:

```bash
monarch accounts list
monarch accounts get ACCOUNT_ID
monarch transactions list --limit 25
monarch transactions get TRANSACTION_ID
monarch receipts list
monarch receipts get RECEIPT_ID
monarch cashflow summary 2026-01-01 2026-05-28
monarch cashflow trends 2026-01-01 2026-05-28
monarch reports data --start-date 2026-01-01 --end-date 2026-05-28
monarch merchants list --search grocery
monarch tags list
monarch household current-user
monarch categories list
monarch recurring list
monarch investments portfolio
monarch goals list
monarch budget get 2026-05
```

Use layered help to explore the command surface:

```bash
monarch --help
monarch auth --help
monarch accounts --help
monarch transactions --help
monarch receipts --help
monarch cashflow --help
monarch reports --help
monarch merchants --help
monarch tags --help
monarch household --help
monarch categories --help
monarch recurring --help
monarch investments --help
monarch goals --help
monarch budget --help
monarch auth login --help
```

## Output

Human-friendly output is the default:

```bash
monarch transactions list --limit 10
```

Use `--json` for machine-readable output:

```bash
monarch transactions list --limit 10 --json
```

Use `--json --raw` when you also want raw response data retained in the JSON:

```bash
monarch transactions get TRANSACTION_ID --json --raw
```

Use `--fields` on a command to show a comma-separated set of output fields.
Dotted paths can select nested values:

```bash
monarch transactions list --fields id,date,amount,notes
monarch transactions list --json --fields id,merchant.name,category.name
```

## Development

Run the test suite:

```bash
.venv/bin/python -m pytest
```

Run an individual command while developing:

```bash
.venv/bin/monarch transactions list --limit 5
```

The CLI source lives in `src/monarch_cli`. Group-specific commands live in
`src/monarch_cli/groups`.

## Security

This is an unofficial tool that stores an authenticated Monarch session on your
machine. Treat that session file like a password.

- Do not commit session files, tokens, downloaded receipts, or personal finance
  exports.
- Prefer `--json` carefully in scripts, since output may include sensitive
  account, transaction, budget, or household data.
- Report security-sensitive issues privately instead of opening a public issue
  with credentials or personal financial data.

## License

MIT License. See [LICENSE](LICENSE).
