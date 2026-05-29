from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Any

import typer
from monarch_api import (
    CategoryType,
    Transaction,
    TransactionAttachment,
    TransactionFilter,
    TransactionPage,
    TransactionReviewStatus,
    TransactionSort,
    TransactionSplit,
    TransactionSplitDetails,
    TransactionSplitDraft,
    TransactionVisibility,
    create_transaction,
    delete_transaction,
    delete_transaction_attachment,
    download_transaction_attachment,
    get_transaction,
    get_transaction_attachment,
    get_transaction_splits,
    list_transaction_attachments,
    list_transactions,
    unsplit_transaction,
    update_transaction,
    update_transaction_splits,
    upload_transaction_attachment,
)

from monarch_cli.errors import handle_cli_errors
from monarch_cli.input import load_json_argument
from monarch_cli.options import JsonOption, RawOption, OutputFieldsOption, SessionPathOption, TrueFalseFilter
from monarch_cli.output import (
    format_bool,
    format_bytes,
    format_money,
    print_key_values,
    print_success,
    print_table,
    print_warning,
    render_json,
)
from monarch_cli.session import require_session

app = typer.Typer(
    help="Search, inspect, edit, split, and attach files to transactions.",
    no_args_is_help=True,
)


class ReportVisibility(str, Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"


class TransactionVisibilityChoice(str, Enum):
    ALL = "all"
    VISIBLE = "visible"
    HIDDEN = "hidden"


TransactionIdsOption = Annotated[
    list[str] | None,
    typer.Option("--transaction-id", help="Only include this transaction. Repeatable."),
]
AccountIdsOption = Annotated[
    list[str] | None,
    typer.Option("--account-id", help="Only include this account. Repeatable."),
]
CategoryIdsOption = Annotated[
    list[str] | None,
    typer.Option("--category-id", help="Only include this category. Repeatable."),
]
CategoryGroupIdsOption = Annotated[
    list[str] | None,
    typer.Option("--category-group-id", help="Only include this category group. Repeatable."),
]
MerchantIdsOption = Annotated[
    list[str] | None,
    typer.Option("--merchant-id", help="Only include this merchant. Repeatable."),
]
TagIdsOption = Annotated[
    list[str] | None,
    typer.Option("--tag-id", help="Only include this tag. Repeatable."),
]
UpdateTagIdsOption = Annotated[
    list[str] | None,
    typer.Option("--tag-id", help="Assign this tag. Repeatable."),
]
GoalIdsOption = Annotated[
    list[str] | None,
    typer.Option("--goal-id", help="Only include this goal. Repeatable."),
]


@app.command("list")
@handle_cli_errors
def list_command(
    session_path: SessionPathOption = None,
    start_date: Annotated[str | None, typer.Option("--start-date", help="Start date.")] = None,
    end_date: Annotated[str | None, typer.Option("--end-date", help="End date.")] = None,
    search: Annotated[str | None, typer.Option("--search", help="Search text.")] = None,
    transaction_ids: TransactionIdsOption = None,
    account_ids: AccountIdsOption = None,
    category_ids: CategoryIdsOption = None,
    category_group_ids: CategoryGroupIdsOption = None,
    merchant_ids: MerchantIdsOption = None,
    tag_ids: TagIdsOption = None,
    goal_ids: GoalIdsOption = None,
    min_amount: Annotated[
        float | None,
        typer.Option("--min-amount", help="Minimum absolute amount."),
    ] = None,
    max_amount: Annotated[
        float | None,
        typer.Option("--max-amount", help="Maximum absolute amount."),
    ] = None,
    category_type: Annotated[
        CategoryType | None,
        typer.Option("--category-type", help="Category type."),
    ] = None,
    credits_only: Annotated[bool, typer.Option("--credits-only", help="Only credits.")] = False,
    debits_only: Annotated[bool, typer.Option("--debits-only", help="Only debits.")] = False,
    pending: Annotated[
        TrueFalseFilter | None,
        typer.Option("--pending", help="Filter by pending status."),
    ] = None,
    recurring: Annotated[
        TrueFalseFilter | None,
        typer.Option("--recurring", help="Filter by recurring status."),
    ] = None,
    split: Annotated[
        TrueFalseFilter | None,
        typer.Option("--split", help="Filter by split status."),
    ] = None,
    uncategorized: Annotated[
        TrueFalseFilter | None,
        typer.Option("--uncategorized", help="Filter by uncategorized status."),
    ] = None,
    untagged: Annotated[
        TrueFalseFilter | None,
        typer.Option("--untagged", help="Filter by untagged status."),
    ] = None,
    has_notes: Annotated[
        TrueFalseFilter | None,
        typer.Option("--has-notes", help="Filter by whether notes are present."),
    ] = None,
    has_attachments: Annotated[
        TrueFalseFilter | None,
        typer.Option("--has-attachments", help="Filter by whether attachments are present."),
    ] = None,
    hidden_from_reports: Annotated[
        TrueFalseFilter | None,
        typer.Option("--hidden-from-reports", help="Filter by report visibility."),
    ] = None,
    needs_review: Annotated[
        TrueFalseFilter | None,
        typer.Option("--needs-review", help="Filter by review status."),
    ] = None,
    needs_review_by_user_id: Annotated[
        str | None,
        typer.Option("--needs-review-by-user-id", help="Needs-review assignee user id."),
    ] = None,
    needs_review_unassigned: Annotated[
        TrueFalseFilter | None,
        typer.Option("--needs-review-unassigned", help="Filter by unassigned review status."),
    ] = None,
    synced_from_institution: Annotated[
        TrueFalseFilter | None,
        typer.Option("--synced-from-institution", help="Filter by institution sync status."),
    ] = None,
    imported_from_mint: Annotated[
        TrueFalseFilter | None,
        typer.Option("--imported-from-mint", help="Filter by Mint import status."),
    ] = None,
    visibility: Annotated[
        TransactionVisibilityChoice | None,
        typer.Option("--visibility", help="Transaction visibility filter."),
    ] = None,
    limit: Annotated[int, typer.Option("--limit", help="Number of transactions to return.")] = 100,
    offset: Annotated[int, typer.Option("--offset", help="Number of transactions to skip.")] = 0,
    sort: Annotated[
        TransactionSort,
        typer.Option("--sort", help="Sort order."),
    ] = TransactionSort.DATE_DESCENDING,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """List transactions."""
    session = require_session(session_path)
    page = list_transactions(
        session,
        filters=_transaction_filter(
            start_date=start_date,
            end_date=end_date,
            search=search,
            transaction_ids=transaction_ids,
            account_ids=account_ids,
            category_ids=category_ids,
            category_group_ids=category_group_ids,
            merchant_ids=merchant_ids,
            tag_ids=tag_ids,
            goal_ids=goal_ids,
            min_amount=min_amount,
            max_amount=max_amount,
            category_type=category_type,
            credits_only=credits_only,
            debits_only=debits_only,
            pending=pending,
            recurring=recurring,
            split=split,
            uncategorized=uncategorized,
            untagged=untagged,
            has_notes=has_notes,
            has_attachments=has_attachments,
            hidden_from_reports=hidden_from_reports,
            needs_review=needs_review,
            needs_review_by_user_id=needs_review_by_user_id,
            needs_review_unassigned=needs_review_unassigned,
            synced_from_institution=synced_from_institution,
            imported_from_mint=imported_from_mint,
            visibility=visibility,
        ),
        limit=limit,
        offset=offset,
        sort=sort,
    )
    if json_output:
        render_json(page, include_raw=raw_output)
        return
    print_table(
        f"Transactions ({page.total_count} total)",
        _TRANSACTION_COLUMNS,
        (_transaction_row(transaction) for transaction in page.transactions),
        source_rows=page.transactions,
    )


@app.command("get")
@handle_cli_errors
def get_command(
    transaction_id: Annotated[str, typer.Argument(help="Transaction id.")],
    session_path: SessionPathOption = None,
    no_redirect_posted: Annotated[
        bool,
        typer.Option("--no-redirect-posted", help="Do not redirect pending items to posted."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Show one transaction."""
    session = require_session(session_path)
    transaction = get_transaction(
        session,
        transaction_id,
        redirect_posted=not no_redirect_posted,
    )
    if transaction is None:
        print_warning(f"No transaction found for id {transaction_id}.")
        raise typer.Exit(1)
    if json_output:
        render_json(transaction, include_raw=raw_output)
        return
    print_key_values("Transaction", _transaction_details(transaction))


@app.command("create")
@handle_cli_errors
def create_command(
    account_id: Annotated[str, typer.Option("--account-id", help="Account id.")],
    amount: Annotated[float, typer.Option("--amount", help="Transaction amount.")],
    date: Annotated[str, typer.Option("--date", help="Transaction date.")],
    merchant_name: Annotated[str, typer.Option("--merchant-name", help="Merchant name.")],
    category_id: Annotated[str, typer.Option("--category-id", help="Category id.")],
    session_path: SessionPathOption = None,
    notes: Annotated[str | None, typer.Option("--notes", help="Transaction notes.")] = None,
    owner_user_id: Annotated[
        str | None,
        typer.Option("--owner-user-id", help="Owner user id."),
    ] = None,
    update_balance: Annotated[
        bool,
        typer.Option("--update-balance", help="Update the account balance."),
    ] = False,
    goal_id: Annotated[str | None, typer.Option("--goal-id", help="Goal id.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Create a manual transaction."""
    session = require_session(session_path)
    transaction = create_transaction(
        session,
        account_id=account_id,
        amount=amount,
        date=date,
        merchant_name=merchant_name,
        category_id=category_id,
        notes=notes,
        owner_user_id=owner_user_id,
        should_update_balance=True if update_balance else None,
        goal_id=goal_id,
    )
    if json_output:
        render_json(transaction, include_raw=raw_output)
        return
    print_key_values("Transaction Created", _transaction_details(transaction))


@app.command("update")
@handle_cli_errors
def update_command(
    transaction_id: Annotated[str, typer.Argument(help="Transaction id.")],
    session_path: SessionPathOption = None,
    date: Annotated[str | None, typer.Option("--date", help="Transaction date.")] = None,
    amount: Annotated[float | None, typer.Option("--amount", help="Transaction amount.")] = None,
    account_id: Annotated[str | None, typer.Option("--account-id", help="Account id.")] = None,
    merchant_name: Annotated[
        str | None,
        typer.Option("--merchant-name", help="Merchant name."),
    ] = None,
    category_id: Annotated[str | None, typer.Option("--category-id", help="Category id.")] = None,
    notes: Annotated[str | None, typer.Option("--notes", help="Transaction notes.")] = None,
    report_visibility: Annotated[
        ReportVisibility | None,
        typer.Option("--report-visibility", help="Whether this appears in reports."),
    ] = None,
    review_status: Annotated[
        TransactionReviewStatus | None,
        typer.Option("--review-status", help="Review status."),
    ] = None,
    needs_review_by_user_id: Annotated[
        str | None,
        typer.Option("--needs-review-by-user-id", help="Needs-review assignee user id."),
    ] = None,
    owner_user_id: Annotated[
        str | None,
        typer.Option("--owner-user-id", help="Owner user id."),
    ] = None,
    tag_ids: UpdateTagIdsOption = None,
    goal_id: Annotated[str | None, typer.Option("--goal-id", help="Goal id.")] = None,
    clear_goal: Annotated[bool, typer.Option("--clear-goal", help="Remove goal link.")] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Update a transaction."""
    session = require_session(session_path)
    transaction = update_transaction(
        session,
        transaction_id,
        date=date,
        amount=amount,
        account_id=account_id,
        merchant_name=merchant_name,
        category_id=category_id,
        notes=notes,
        hide_from_reports=_hide_from_reports_value(report_visibility),
        review_status=review_status,
        needs_review_by_user_id=needs_review_by_user_id,
        owner_user_id=owner_user_id,
        tag_ids=tag_ids,
        goal_id=goal_id,
        clear_goal=clear_goal,
    )
    if json_output:
        render_json(transaction, include_raw=raw_output)
        return
    print_key_values("Transaction Updated", _transaction_details(transaction))


@app.command("delete")
@handle_cli_errors
def delete_command(
    transaction_id: Annotated[str, typer.Argument(help="Transaction id.")],
    session_path: SessionPathOption = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Delete a transaction."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Delete transaction {transaction_id}?"):
        print_warning("Transaction left unchanged.")
        return
    deleted = delete_transaction(session, transaction_id)
    if json_output:
        render_json({"transaction_id": transaction_id, "deleted": deleted})
        return
    if deleted:
        print_success("Transaction deleted.")
    else:
        print_warning("Transaction was not deleted.")


@app.command("get-splits")
@handle_cli_errors
def get_splits_command(
    transaction_id: Annotated[str, typer.Argument(help="Transaction id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Show split details for a transaction."""
    session = require_session(session_path)
    details = get_transaction_splits(session, transaction_id)
    if details is None:
        print_warning(f"No transaction found for id {transaction_id}.")
        raise typer.Exit(1)
    if json_output:
        render_json(details, include_raw=raw_output)
        return
    print_table("Transaction Splits", _SPLIT_COLUMNS, (_split_row(split) for split in details.splits), source_rows=details.splits)


@app.command("update-splits")
@handle_cli_errors
def update_splits_command(
    transaction_id: Annotated[str, typer.Argument(help="Transaction id.")],
    session_path: SessionPathOption = None,
    splits_json: Annotated[
        str | None,
        typer.Option("--splits-json", help="JSON array of split rows."),
    ] = None,
    splits_file: Annotated[
        Path | None,
        typer.Option("--splits-file", help="Path to a JSON file of split rows."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Replace transaction splits."""
    session = require_session(session_path)
    split_data = load_json_argument(splits_json, splits_file)
    details = update_transaction_splits(
        session,
        transaction_id,
        _split_drafts(split_data),
    )
    if json_output:
        render_json(details, include_raw=raw_output)
        return
    print_table("Transaction Splits Updated", _SPLIT_COLUMNS, (_split_row(split) for split in details.splits), source_rows=details.splits)


@app.command("unsplit")
@handle_cli_errors
def unsplit_command(
    transaction_id: Annotated[str, typer.Argument(help="Transaction id.")],
    session_path: SessionPathOption = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Remove transaction splits."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Remove splits from transaction {transaction_id}?"):
        print_warning("Transaction left unchanged.")
        return
    details = unsplit_transaction(session, transaction_id)
    if json_output:
        render_json(details, include_raw=raw_output)
        return
    print_table("Transaction Splits Removed", _SPLIT_COLUMNS, (_split_row(split) for split in details.splits), source_rows=details.splits)


@app.command("list-attachments")
@handle_cli_errors
def list_attachments_command(
    transaction_id: Annotated[str, typer.Argument(help="Transaction id.")],
    session_path: SessionPathOption = None,
    no_redirect_posted: Annotated[
        bool,
        typer.Option("--no-redirect-posted", help="Do not redirect pending items to posted."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """List attachments for a transaction."""
    session = require_session(session_path)
    attachments = list_transaction_attachments(
        session,
        transaction_id,
        redirect_posted=not no_redirect_posted,
    )
    if json_output:
        render_json(attachments, include_raw=raw_output)
        return
    print_table(
        "Transaction Attachments",
        _ATTACHMENT_COLUMNS,
        (_attachment_row(attachment) for attachment in attachments),
        source_rows=attachments,
    )


@app.command("get-attachment")
@handle_cli_errors
def get_attachment_command(
    attachment_id: Annotated[str, typer.Argument(help="Attachment id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Show one transaction attachment."""
    session = require_session(session_path)
    attachment = get_transaction_attachment(session, attachment_id)
    if attachment is None:
        print_warning(f"No attachment found for id {attachment_id}.")
        raise typer.Exit(1)
    if json_output:
        render_json(attachment, include_raw=raw_output)
        return
    print_key_values("Transaction Attachment", _attachment_details(attachment))


@app.command("upload-attachment")
@handle_cli_errors
def upload_attachment_command(
    transaction_id: Annotated[str, typer.Argument(help="Transaction id.")],
    file_path: Annotated[Path, typer.Argument(help="File to upload.")],
    session_path: SessionPathOption = None,
    filename: Annotated[
        str | None,
        typer.Option("--filename", help="Filename to store in Monarch."),
    ] = None,
    content_type: Annotated[
        str | None,
        typer.Option("--content-type", help="File content type."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Upload a transaction attachment."""
    session = require_session(session_path)
    attachment = upload_transaction_attachment(
        session,
        transaction_id,
        file_path,
        filename=filename,
        content_type=content_type,
    )
    if json_output:
        render_json(attachment, include_raw=raw_output)
        return
    print_key_values("Transaction Attachment Uploaded", _attachment_details(attachment))


@app.command("download-attachment")
@handle_cli_errors
def download_attachment_command(
    attachment_id: Annotated[str, typer.Argument(help="Attachment id.")],
    path: Annotated[
        Path | None,
        typer.Option("--path", help="Destination file or directory."),
    ] = None,
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Download a transaction attachment."""
    session = require_session(session_path)
    content = download_transaction_attachment(session, attachment_id, path=path)
    if json_output:
        render_json(
            {
                "attachment_id": attachment_id,
                "size_bytes": len(content),
                "path": path,
            }
        )
        return
    if path is None:
        print_key_values(
            "Transaction Attachment Downloaded",
            {"attachment_id": attachment_id, "size": format_bytes(len(content))},
        )
    else:
        print_key_values(
            "Transaction Attachment Downloaded",
            {
                "attachment_id": attachment_id,
                "size": format_bytes(len(content)),
                "path": path,
            },
        )


@app.command("delete-attachment")
@handle_cli_errors
def delete_attachment_command(
    attachment_id: Annotated[str, typer.Argument(help="Attachment id.")],
    session_path: SessionPathOption = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Delete a transaction attachment."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Delete attachment {attachment_id}?"):
        print_warning("Attachment left unchanged.")
        return
    deleted = delete_transaction_attachment(session, attachment_id)
    if json_output:
        render_json({"attachment_id": attachment_id, "deleted": deleted})
        return
    if deleted:
        print_success("Attachment deleted.")
    else:
        print_warning("Attachment was not deleted.")


_TRANSACTION_COLUMNS = [
    ("id", "meta"),
    ("date", "muted"),
    ("merchant", ""),
    ("amount", ""),
    ("account", "muted"),
    ("category", "muted"),
    ("review", "muted"),
    ("pending", "muted"),
]
_SPLIT_COLUMNS = [
    ("id", "meta"),
    ("date", "muted"),
    ("merchant", ""),
    ("amount", ""),
    ("category", "muted"),
    ("review", "muted"),
]
_ATTACHMENT_COLUMNS = [
    ("id", "meta"),
    ("filename", ""),
    ("extension", "muted"),
    ("size", "muted"),
    ("public_id", "meta"),
]


def _transaction_filter(
    *,
    start_date: str | None,
    end_date: str | None,
    search: str | None,
    transaction_ids: list[str] | None,
    account_ids: list[str] | None,
    category_ids: list[str] | None,
    category_group_ids: list[str] | None,
    merchant_ids: list[str] | None,
    tag_ids: list[str] | None,
    goal_ids: list[str] | None,
    min_amount: float | None,
    max_amount: float | None,
    category_type: CategoryType | None,
    credits_only: bool,
    debits_only: bool,
    pending: TrueFalseFilter | None,
    recurring: TrueFalseFilter | None,
    split: TrueFalseFilter | None,
    uncategorized: TrueFalseFilter | None,
    untagged: TrueFalseFilter | None,
    has_notes: TrueFalseFilter | None,
    has_attachments: TrueFalseFilter | None,
    hidden_from_reports: TrueFalseFilter | None,
    needs_review: TrueFalseFilter | None,
    needs_review_by_user_id: str | None,
    needs_review_unassigned: TrueFalseFilter | None,
    synced_from_institution: TrueFalseFilter | None,
    imported_from_mint: TrueFalseFilter | None,
    visibility: TransactionVisibilityChoice | None,
) -> TransactionFilter | None:
    values = {
        "start_date": start_date,
        "end_date": end_date,
        "search": search,
        "transaction_ids": transaction_ids,
        "account_ids": account_ids,
        "category_ids": category_ids,
        "category_group_ids": category_group_ids,
        "merchant_ids": merchant_ids,
        "tag_ids": tag_ids,
        "goal_ids": goal_ids,
        "min_absolute_amount": min_amount,
        "max_absolute_amount": max_amount,
        "category_type": category_type,
        "credits_only": True if credits_only else None,
        "debits_only": True if debits_only else None,
        "is_pending": _true_false_value(pending),
        "is_recurring": _true_false_value(recurring),
        "is_split": _true_false_value(split),
        "is_uncategorized": _true_false_value(uncategorized),
        "is_untagged": _true_false_value(untagged),
        "has_notes": _true_false_value(has_notes),
        "has_attachments": _true_false_value(has_attachments),
        "hide_from_reports": _true_false_value(hidden_from_reports),
        "needs_review": _true_false_value(needs_review),
        "needs_review_by_user_id": needs_review_by_user_id,
        "needs_review_unassigned": _true_false_value(needs_review_unassigned),
        "synced_from_institution": _true_false_value(synced_from_institution),
        "imported_from_mint": _true_false_value(imported_from_mint),
        "transaction_visibility": _transaction_visibility(visibility),
    }
    if not any(value is not None and value != [] for value in values.values()):
        return None
    return TransactionFilter(**values)


def _transaction_visibility(
    value: TransactionVisibilityChoice | None,
) -> TransactionVisibility | None:
    if value is None:
        return None
    return {
        TransactionVisibilityChoice.ALL: TransactionVisibility.ALL,
        TransactionVisibilityChoice.VISIBLE: TransactionVisibility.VISIBLE_ONLY,
        TransactionVisibilityChoice.HIDDEN: TransactionVisibility.HIDDEN_ONLY,
    }[value]


def _transaction_row(transaction: Transaction) -> dict[str, object]:
    return {
        "id": transaction.id,
        "date": transaction.date,
        "merchant": transaction.merchant_name,
        "amount": format_money(transaction.amount),
        "account": transaction.account.display_name if transaction.account else None,
        "category": transaction.category.name if transaction.category else None,
        "review": _enum_value(transaction.review_status),
        "pending": format_bool(transaction.pending),
    }


def _transaction_details(transaction: Transaction) -> dict[str, object]:
    return {
        "id": transaction.id,
        "date": transaction.date,
        "amount": format_money(transaction.amount),
        "merchant": transaction.merchant_name,
        "account": transaction.account.display_name if transaction.account else None,
        "category": transaction.category.name if transaction.category else None,
        "tags": ", ".join(tag.name for tag in transaction.tags),
        "notes": transaction.notes,
        "review_status": _enum_value(transaction.review_status),
        "needs_review": format_bool(transaction.needs_review),
        "pending": format_bool(transaction.pending),
        "hide_from_reports": format_bool(transaction.hide_from_reports),
        "split": format_bool(transaction.is_split),
        "has_splits": format_bool(transaction.has_splits),
        "recurring": format_bool(transaction.is_recurring),
        "goal": transaction.goal.name if transaction.goal else None,
        "attachments": transaction.attachment_count,
        "owner": transaction.owner.display_name if transaction.owner else None,
        "updated_at": transaction.updated_at,
    }


def _split_row(split: TransactionSplit) -> dict[str, object]:
    return {
        "id": split.id,
        "date": split.date,
        "merchant": split.merchant_name,
        "amount": format_money(split.amount),
        "category": split.category.name if split.category else None,
        "review": _enum_value(split.review_status),
    }


def _attachment_row(attachment: TransactionAttachment) -> dict[str, object]:
    return {
        "id": attachment.id,
        "filename": attachment.filename,
        "extension": attachment.extension,
        "size": format_bytes(attachment.size_bytes),
        "public_id": attachment.public_id,
    }


def _attachment_details(attachment: TransactionAttachment) -> dict[str, object]:
    return {
        "id": attachment.id,
        "filename": attachment.filename,
        "extension": attachment.extension,
        "size": format_bytes(attachment.size_bytes),
        "public_id": attachment.public_id,
        "url": attachment.original_asset_url,
    }


def _hide_from_reports_value(value: ReportVisibility | None) -> bool | None:
    if value is None:
        return None
    return value == ReportVisibility.HIDDEN


def _true_false_value(value: TrueFalseFilter | None) -> bool | None:
    if value is None:
        return None
    return value == TrueFalseFilter.TRUE


def _split_drafts(data: Any) -> list[TransactionSplitDraft]:
    if not isinstance(data, list):
        raise ValueError("Split input must be a JSON array.")
    drafts = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Split row {index} must be a JSON object.")
        if "amount" not in item:
            raise ValueError(f"Split row {index} must include amount.")
        values = dict(item)
        review_status = values.get("review_status")
        if review_status is not None:
            values["review_status"] = TransactionReviewStatus(review_status)
        drafts.append(TransactionSplitDraft(**values))
    return drafts


def _enum_value(value: object) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))
