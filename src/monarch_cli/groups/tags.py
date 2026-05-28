from __future__ import annotations

from typing import Annotated

import typer
from monarch_api import (
    Tag,
    create_tag,
    delete_tag,
    get_tag,
    list_tags,
    reorder_tag,
    update_tag,
)

from monarch_cli.errors import handle_cli_errors
from monarch_cli.options import JsonOption, RawOption, SessionPathOption
from monarch_cli.output import print_key_values, print_success, print_table, print_warning, render_json
from monarch_cli.session import require_session

app = typer.Typer(
    help="List, inspect, create, update, delete, and reorder tags.",
    no_args_is_help=True,
)


@app.command("list")
@handle_cli_errors
def list_command(
    session_path: SessionPathOption = None,
    search: Annotated[str | None, typer.Option("--search", help="Search text.")] = None,
    limit: Annotated[int | None, typer.Option("--limit", help="Number of tags to return.")] = None,
    include_transaction_count: Annotated[
        bool,
        typer.Option("--include-transaction-count", help="Include transaction counts."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
) -> None:
    """List tags."""
    session = require_session(session_path)
    tags = list_tags(
        session,
        search=search,
        limit=limit,
        include_transaction_count=include_transaction_count,
    )
    if json_output:
        render_json(tags, include_raw=raw_output)
        return
    print_table("Tags", _TAG_COLUMNS, (_tag_row(tag) for tag in tags))


@app.command("get")
@handle_cli_errors
def get_command(
    tag_id: Annotated[str, typer.Argument(help="Tag id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
) -> None:
    """Show one tag."""
    session = require_session(session_path)
    tag = get_tag(session, tag_id)
    if tag is None:
        print_warning(f"No tag found for id {tag_id}.")
        raise typer.Exit(1)
    if json_output:
        render_json(tag, include_raw=raw_output)
        return
    print_key_values("Tag", _tag_details(tag))


@app.command("create")
@handle_cli_errors
def create_command(
    name: Annotated[str, typer.Option("--name", help="Tag name.")],
    color: Annotated[str, typer.Option("--color", help="Tag color.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
) -> None:
    """Create a tag."""
    session = require_session(session_path)
    tag = create_tag(session, name=name, color=color)
    if json_output:
        render_json(tag, include_raw=raw_output)
        return
    print_key_values("Tag Created", _tag_details(tag))


@app.command("update")
@handle_cli_errors
def update_command(
    tag_id: Annotated[str, typer.Argument(help="Tag id.")],
    session_path: SessionPathOption = None,
    name: Annotated[str | None, typer.Option("--name", help="Tag name.")] = None,
    color: Annotated[str | None, typer.Option("--color", help="Tag color.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
) -> None:
    """Update a tag."""
    session = require_session(session_path)
    tag = update_tag(session, tag_id, name=name, color=color)
    if json_output:
        render_json(tag, include_raw=raw_output)
        return
    print_key_values("Tag Updated", _tag_details(tag))


@app.command("delete")
@handle_cli_errors
def delete_command(
    tag_id: Annotated[str, typer.Argument(help="Tag id.")],
    session_path: SessionPathOption = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
    json_output: JsonOption = False,
) -> None:
    """Delete a tag."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Delete tag {tag_id}?"):
        print_warning("Tag left unchanged.")
        return
    deleted = delete_tag(session, tag_id)
    if json_output:
        render_json({"tag_id": tag_id, "deleted": deleted})
        return
    if deleted:
        print_success("Tag deleted.")
    else:
        print_warning("Tag was not deleted.")


@app.command("reorder")
@handle_cli_errors
def reorder_command(
    tag_id: Annotated[str, typer.Argument(help="Tag id.")],
    order: Annotated[int, typer.Option("--order", help="New sort order.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
) -> None:
    """Reorder a tag."""
    session = require_session(session_path)
    tags = reorder_tag(session, tag_id, order=order)
    if json_output:
        render_json(tags, include_raw=raw_output)
        return
    print_table("Tags Reordered", _TAG_COLUMNS, (_tag_row(tag) for tag in tags))


_TAG_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("color", "muted"),
    ("order", "muted"),
    ("transactions", "muted"),
]


def _tag_row(tag: Tag) -> dict[str, object]:
    return {
        "id": tag.id,
        "name": tag.name,
        "color": tag.color,
        "order": tag.order,
        "transactions": tag.transaction_count,
    }


def _tag_details(tag: Tag) -> dict[str, object]:
    return {
        "id": tag.id,
        "name": tag.name,
        "color": tag.color,
        "order": tag.order,
        "transactions": tag.transaction_count,
    }
