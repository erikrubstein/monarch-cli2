from __future__ import annotations

from typing import Annotated

import typer
from monarch_api import (
    Category,
    CategoryCatalog,
    CategoryFilter,
    CategoryGroup,
    CategoryType,
    create_category,
    create_category_group,
    delete_category_group,
    get_category,
    get_category_catalog,
    get_category_group,
    list_categories,
    list_category_groups,
    reactivate_category,
    remove_category,
    reorder_category,
    reorder_category_group,
    update_category,
    update_category_group,
)

from monarch_cli.errors import handle_cli_errors, raise_cli_error
from monarch_cli.options import JsonOption, RawOption, OutputFieldsOption, AppendFieldsOption, SessionPathOption
from monarch_cli.output import format_bool, print_key_values, print_success, print_table, print_warning, render_json
from monarch_cli.session import require_session

app = typer.Typer(
    help="Manage category groups and categories.",
    no_args_is_help=True,
)

GroupIdsOption = Annotated[
    list[str] | None,
    typer.Option("--group-id", help="Only include this group. Repeatable."),
]
TypesOption = Annotated[
    list[CategoryType] | None,
    typer.Option("--type", help="Only include this category type. Repeatable."),
]


@app.command("list")
@handle_cli_errors
def list_command(
    session_path: SessionPathOption = None,
    group_ids: GroupIdsOption = None,
    types: TypesOption = None,
    include_disabled: Annotated[
        bool,
        typer.Option("--include-disabled", help="Include disabled categories."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """List categories."""
    session = require_session(session_path)
    categories = list_categories(
        session,
        filters=_category_filter(group_ids=group_ids, types=types),
        include_disabled=include_disabled,
    )
    if json_output:
        render_json(categories, include_raw=raw_output)
        return
    print_table("Categories", _CATEGORY_COLUMNS, (_category_row(category) for category in categories), source_rows=categories)


@app.command("list-groups")
@handle_cli_errors
def list_groups_command(
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """List category groups."""
    session = require_session(session_path)
    groups = list_category_groups(session)
    if json_output:
        render_json(groups, include_raw=raw_output)
        return
    print_table("Category Groups", _GROUP_COLUMNS, (_group_row(group) for group in groups), source_rows=groups)


@app.command("catalog")
@handle_cli_errors
def catalog_command(
    session_path: SessionPathOption = None,
    include_disabled: Annotated[
        bool,
        typer.Option("--include-disabled", help="Include disabled categories."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show the category catalog."""
    session = require_session(session_path)
    catalog = get_category_catalog(session, include_disabled=include_disabled)
    if json_output:
        render_json(catalog, include_raw=raw_output)
        return
    print_table("Category Groups", _GROUP_COLUMNS, (_group_row(group) for group in catalog.groups), source_rows=catalog.groups)
    print_table("Categories", _CATEGORY_COLUMNS, (_category_row(category) for category in catalog.categories), source_rows=catalog.categories)


@app.command("get")
@handle_cli_errors
def get_command(
    category_id: Annotated[str, typer.Argument(help="Category id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show one category."""
    session = require_session(session_path)
    category = get_category(session, category_id)
    if category is None:
        raise_cli_error(f"No category found for id {category_id}.")
    if json_output:
        render_json(category, include_raw=raw_output)
        return
    print_key_values("Category", _category_details(category))


@app.command("get-group")
@handle_cli_errors
def get_group_command(
    group_id: Annotated[str, typer.Argument(help="Category group id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show one category group."""
    session = require_session(session_path)
    group = get_category_group(session, group_id)
    if group is None:
        raise_cli_error(f"No category group found for id {group_id}.")
    if json_output:
        render_json(group, include_raw=raw_output)
        return
    print_key_values("Category Group", _group_details(group))


@app.command("create")
@handle_cli_errors
def create_command(
    name: Annotated[str, typer.Option("--name", help="Category name.")],
    group_id: Annotated[str, typer.Option("--group-id", help="Category group id.")],
    icon: Annotated[str, typer.Option("--icon", help="Category icon.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Create a category."""
    session = require_session(session_path)
    category = create_category(session, name=name, group_id=group_id, icon=icon)
    if json_output:
        render_json(category, include_raw=raw_output)
        return
    print_key_values("Category Created", _category_details(category))


@app.command("update")
@handle_cli_errors
def update_command(
    category_id: Annotated[str, typer.Argument(help="Category id.")],
    session_path: SessionPathOption = None,
    name: Annotated[str | None, typer.Option("--name", help="Category name.")] = None,
    group_id: Annotated[str | None, typer.Option("--group-id", help="Category group id.")] = None,
    icon: Annotated[str | None, typer.Option("--icon", help="Category icon.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update a category."""
    session = require_session(session_path)
    category = update_category(session, category_id, name=name, group_id=group_id, icon=icon)
    if json_output:
        render_json(category, include_raw=raw_output)
        return
    print_key_values("Category Updated", _category_details(category))


@app.command("remove")
@handle_cli_errors
def remove_command(
    category_id: Annotated[str, typer.Argument(help="Category id.")],
    session_path: SessionPathOption = None,
    move_to_category_id: Annotated[
        str | None,
        typer.Option("--move-to-category-id", help="Move related data to this category."),
    ] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the confirmation prompt.")] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Remove a category."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Remove category {category_id}?"):
        print_warning("Category left unchanged.")
        return
    removed = remove_category(session, category_id, move_to_category_id=move_to_category_id)
    if json_output:
        render_json({"category_id": category_id, "removed": removed})
        return
    if removed:
        print_success("Category removed.")
    else:
        print_warning("Category was not removed.")


@app.command("reactivate")
@handle_cli_errors
def reactivate_command(
    category_id: Annotated[str, typer.Argument(help="Category id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Reactivate a category."""
    session = require_session(session_path)
    category = reactivate_category(session, category_id)
    if json_output:
        render_json(category, include_raw=raw_output)
        return
    print_key_values("Category Reactivated", _category_details(category))


@app.command("reorder")
@handle_cli_errors
def reorder_command(
    category_id: Annotated[str, typer.Argument(help="Category id.")],
    group_id: Annotated[str, typer.Option("--group-id", help="Category group id.")],
    order: Annotated[int, typer.Option("--order", help="New sort order.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Reorder a category."""
    session = require_session(session_path)
    category = reorder_category(session, category_id, group_id=group_id, order=order)
    if json_output:
        render_json(category, include_raw=raw_output)
        return
    print_key_values("Category Reordered", _category_details(category))


@app.command("create-group")
@handle_cli_errors
def create_group_command(
    name: Annotated[str, typer.Option("--name", help="Category group name.")],
    category_type: Annotated[CategoryType, typer.Option("--type", help="Category group type.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Create a category group."""
    session = require_session(session_path)
    group = create_category_group(session, name=name, type=category_type)
    if json_output:
        render_json(group, include_raw=raw_output)
        return
    print_key_values("Category Group Created", _group_details(group))


@app.command("update-group")
@handle_cli_errors
def update_group_command(
    group_id: Annotated[str, typer.Argument(help="Category group id.")],
    session_path: SessionPathOption = None,
    name: Annotated[str | None, typer.Option("--name", help="Category group name.")] = None,
    category_type: Annotated[
        CategoryType | None,
        typer.Option("--type", help="Category group type."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update a category group."""
    session = require_session(session_path)
    group = update_category_group(session, group_id, name=name, type=category_type)
    if json_output:
        render_json(group, include_raw=raw_output)
        return
    print_key_values("Category Group Updated", _group_details(group))


@app.command("delete-group")
@handle_cli_errors
def delete_group_command(
    group_id: Annotated[str, typer.Argument(help="Category group id.")],
    session_path: SessionPathOption = None,
    move_to_group_id: Annotated[
        str | None,
        typer.Option("--move-to-group-id", help="Move categories to this group."),
    ] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the confirmation prompt.")] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Delete a category group."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Delete category group {group_id}?"):
        print_warning("Category group left unchanged.")
        return
    deleted = delete_category_group(session, group_id, move_to_group_id=move_to_group_id)
    if json_output:
        render_json({"group_id": group_id, "deleted": deleted})
        return
    if deleted:
        print_success("Category group deleted.")
    else:
        print_warning("Category group was not deleted.")


@app.command("reorder-group")
@handle_cli_errors
def reorder_group_command(
    group_id: Annotated[str, typer.Argument(help="Category group id.")],
    order: Annotated[int, typer.Option("--order", help="New sort order.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Reorder a category group."""
    session = require_session(session_path)
    groups = reorder_category_group(session, group_id, order=order)
    if json_output:
        render_json(groups, include_raw=raw_output)
        return
    print_table("Category Groups Reordered", _GROUP_COLUMNS, (_group_row(group) for group in groups), source_rows=groups)


_CATEGORY_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("group", "muted"),
    ("type", "muted"),
    ("order", "muted"),
    ("disabled", "muted"),
    ("budget", "muted"),
]
_GROUP_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("type", "muted"),
    ("order", "muted"),
    ("budgeting", "muted"),
]


def _category_filter(
    *,
    group_ids: list[str] | None,
    types: list[CategoryType] | None,
) -> CategoryFilter | None:
    if not group_ids and not types:
        return None
    return CategoryFilter(group_ids=group_ids, types=types)


def _category_row(category: Category) -> dict[str, object]:
    return {
        "id": category.id,
        "name": category.name,
        "group": category.group.name if category.group else None,
        "type": _enum_value(category.type),
        "order": category.order,
        "disabled": format_bool(category.is_disabled),
        "budget": category.budget_variability,
    }


def _category_details(category: Category) -> dict[str, object]:
    return {
        "id": category.id,
        "name": category.name,
        "icon": category.icon,
        "group": category.group.name if category.group else None,
        "group_id": category.group.id if category.group else None,
        "type": _enum_value(category.type),
        "order": category.order,
        "system": format_bool(category.is_system),
        "disabled": format_bool(category.is_disabled),
        "protected": format_bool(category.is_protected),
        "exclude_from_budget": format_bool(category.exclude_from_budget),
        "budget_variability": category.budget_variability,
    }


def _group_row(group: CategoryGroup) -> dict[str, object]:
    return {
        "id": group.id,
        "name": group.name,
        "type": _enum_value(group.type),
        "order": group.order,
        "budgeting": format_bool(group.group_level_budgeting_enabled),
    }


def _group_details(group: CategoryGroup) -> dict[str, object]:
    return {
        "id": group.id,
        "name": group.name,
        "type": _enum_value(group.type),
        "order": group.order,
        "color": group.color,
        "group_level_budgeting_enabled": format_bool(group.group_level_budgeting_enabled),
        "budget_variability": group.budget_variability,
    }


def _enum_value(value: object) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))
