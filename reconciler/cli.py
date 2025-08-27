from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime
from typing import List, Sequence

from .loader import load_transactions, Transaction
from .matcher import CombinedMatcher, ExactMatcher, reconcile


def parse_file_spec(spec: str):
    """Parse file specification of the form path[:amount[:date[:description]]]."""
    parts = spec.split(":")
    path = parts[0]
    amount_col = parts[1] if len(parts) > 1 and parts[1] else "Amount"
    date_col = parts[2] if len(parts) > 2 and parts[2] else "Date"
    description_col = parts[3] if len(parts) > 3 and parts[3] else "Description"
    return path, amount_col, date_col, description_col


def load_from_specs(specs: Sequence[str]) -> List[Transaction]:
    txns: List[Transaction] = []
    for spec in specs:
        path, amount, date_col, desc = parse_file_spec(spec)
        txns.extend(load_transactions(path, amount, date_col, desc))
    return txns


def filter_transactions(
    transactions: Sequence[Transaction],
    start: datetime | None,
    end: datetime | None,
    ignore: Sequence[str],
) -> List[Transaction]:
    result: List[Transaction] = []
    for tx in transactions:
        if start and tx.date and tx.date < start.date():
            continue
        if end and tx.date and tx.date > end.date():
            continue
        desc_lower = tx.description.lower()
        if any(word.lower() in desc_lower for word in ignore):
            continue
        result.append(tx)
    return result


def print_transactions(transactions: Sequence[Transaction]):
    if not transactions:
        print("  None")
        return
    # determine all columns
    columns = sorted({col for tx in transactions for col in tx.data.keys()})
    widths = {col: max(len(col), *(len(tx.data.get(col, "")) for tx in transactions)) for col in columns}
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    divider = "-+-".join("-" * widths[col] for col in columns)
    print(header)
    print(divider)
    for tx in transactions:
        row = " | ".join(tx.data.get(col, "").ljust(widths[col]) for col in columns)
        print(row)


def main(argv: Sequence[str] | None = None):
    parser = argparse.ArgumentParser(description="Reconcile transactions with a credit card statement")
    parser.add_argument(
        "--transactions",
        action="append",
        required=True,
        help="Transaction file specification: path[:amount_col[:date_col[:description_col]]]",
    )
    parser.add_argument(
        "--statement",
        required=True,
        help="Credit card statement file specification: path[:amount_col[:date_col[:description_col]]]",
    )
    parser.add_argument("--ignore", action="append", default=[], help="Ignore statement rows containing this text")
    parser.add_argument("--start", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", help="End date YYYY-MM-DD")
    parser.add_argument("--allow-combined", action="store_true", help="Allow matching combined charges")
    parser.add_argument(
        "--statement-charges-positive",
        action="store_true",
        help="Statement lists charges as positive amounts (default assumes negatives)",
    )

    args = parser.parse_args(argv)

    statement_path, s_amount, s_date, s_desc = parse_file_spec(args.statement)
    statement = load_transactions(statement_path, s_amount, s_date, s_desc)
    if not args.statement_charges_positive:
        statement = [replace(tx, amount=-tx.amount) for tx in statement]
    statement = [tx for tx in statement if tx.amount >= 0]

    transactions = load_from_specs(args.transactions)

    # Determine date range
    start = datetime.fromisoformat(args.start) if args.start else None
    end = datetime.fromisoformat(args.end) if args.end else None
    if not start or not end:
        stmt_dates = [tx.date for tx in statement if tx.date]
        if stmt_dates:
            if not start:
                start = datetime.combine(min(stmt_dates), datetime.min.time())
            if not end:
                end = datetime.combine(max(stmt_dates), datetime.min.time())

    statement = filter_transactions(statement, start, end, args.ignore)
    transactions = filter_transactions(transactions, start, end, [])

    matcher = CombinedMatcher() if args.allow_combined else ExactMatcher()
    matched, only_statement, only_ledger = reconcile(statement, transactions, matcher)

    if not only_statement and not only_ledger:
        print("All transactions match")
        return
    if only_statement:
        print("Transactions only on credit card statement:")
        print_transactions(only_statement)
    if only_ledger:
        print("Transactions only on provided lists:")
        print_transactions(only_ledger)


if __name__ == "__main__":
    main()
