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
```

Use layered help to drill into the CLI:

```bash
monarch --help
monarch auth --help
monarch accounts --help
monarch auth login --help
```
