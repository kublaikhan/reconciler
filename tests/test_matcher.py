from dataclasses import replace
from decimal import Decimal

from reconciler.loader import load_transactions
from reconciler.matcher import CombinedMatcher, ExactMatcher


def test_exact_matcher_separates_unmatched_transactions():
    statement = load_transactions(
        "tests/data/statement.csv", "Amount", "Date", "Description"
    )
    statement = [replace(tx, amount=-tx.amount) for tx in statement]
    ledger = load_transactions(
        "tests/data/ledger.csv", "Amount", "Date", "Description"
    )
    matcher = ExactMatcher()
    matched, only_statement, only_ledger = matcher.match(statement, ledger)

    assert len(matched) == 2
    assert [tx.description for tx, _ in matched] == ["Coffee Shop", "Online Store"]
    assert [tx.description for tx in only_statement] == ["Grocery"]
    assert [tx.description for tx in only_ledger] == ["Grocery", "Grocery"]


def test_combined_matcher_matches_split_transactions():
    statement = load_transactions(
        "tests/data/statement.csv", "Amount", "Date", "Description"
    )
    statement = [replace(tx, amount=-tx.amount) for tx in statement]
    ledger = load_transactions(
        "tests/data/ledger.csv", "Amount", "Date", "Description"
    )
    matcher = CombinedMatcher()
    matched, only_statement, only_ledger = matcher.match(statement, ledger)

    assert len(matched) == 3
    assert not only_statement
    assert not only_ledger

    grocery_match = next(
        (combo for st, combo in matched if st.description == "Grocery"), None
    )
    assert grocery_match is not None
    amounts = sorted(tx.amount for tx in grocery_match)
    assert amounts == [Decimal("4.00"), Decimal("6.00")]
    assert all(isinstance(tx.amount, Decimal) for st, combo in matched for tx in [st, *combo])
