# monarch-cli2

Unofficial command line interface for Monarch Money.

This project is not affiliated with Monarch Money.

## Development

From this checkout, with `monarch-api2` cloned next to it:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install httpx typer rich pytest
.venv/bin/python -m pip install -e ../monarch-api2
.venv/bin/python -m pip install --no-deps -e .
```

## Usage

```bash
monarch auth login you@example.com
monarch auth status
monarch auth export ~/monarch-session.json
monarch auth logout
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
```

Use layered help to drill into the CLI:

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
monarch auth login --help
```
