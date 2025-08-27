from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from decimal import Decimal
from typing import List, Sequence, Tuple

from .loader import Transaction


class Matcher(ABC):
    """Interface for reconciling two transaction lists."""

    @abstractmethod
    def match(
        self, statement: Sequence[Transaction], ledger: Sequence[Transaction]
    ) -> Tuple[List[Tuple[Transaction, Sequence[Transaction]]], List[Transaction], List[Transaction]]:
        """Return a tuple of (matched, only_statement, only_ledger)."""
        raise NotImplementedError


class ExactMatcher(Matcher):
    """Performs one-to-one exact matching based on transaction keys."""

    def match(
        self, statement: Sequence[Transaction], ledger: Sequence[Transaction]
    ) -> Tuple[List[Tuple[Transaction, Sequence[Transaction]]], List[Transaction], List[Transaction]]:
        ledger_map = defaultdict(list)
        for txn in ledger:
            ledger_map[txn.key()].append(txn)

        matched: List[Tuple[Transaction, Sequence[Transaction]]] = []
        statement_only: List[Transaction] = []
        for st in statement:
            key = st.key()
            if ledger_map[key]:
                matched.append((st, [ledger_map[key].pop(0)]))
            else:
                statement_only.append(st)
        ledger_only = [tx for txns in ledger_map.values() for tx in txns]
        return matched, statement_only, ledger_only


class CombinedMatcher(ExactMatcher):
    """Matcher that allows combining multiple statement entries to match a ledger entry."""

    def match(
        self, statement: Sequence[Transaction], ledger: Sequence[Transaction]
    ) -> Tuple[List[Tuple[Transaction, Sequence[Transaction]]], List[Transaction], List[Transaction]]:
        matched, statement_only, ledger_only = super().match(statement, ledger)
        if not statement_only or not ledger_only:
            return matched, statement_only, ledger_only

        remaining_statement = statement_only[:]
        remaining_ledger: List[Transaction] = []
        for le in ledger_only:
            combo = _find_combination(remaining_statement, le)
            if combo:
                for item in combo:
                    remaining_statement.remove(item)
                matched.append((le, combo))
            else:
                remaining_ledger.append(le)
        return matched, remaining_statement, remaining_ledger


def _find_combination(ledger: List[Transaction], target: Transaction) -> List[Transaction]:
    """Return a subset of ledger transactions whose amounts sum to the target."""
    candidates = ledger
    max_items = min(5, len(candidates))
    from itertools import combinations

    for r in range(2, max_items + 1):
        for combo in combinations(candidates, r):
            total = sum((tx.amount for tx in combo), Decimal("0"))
            if total == target.amount:
                return list(combo)
    return []


def reconcile(
    statement: Sequence[Transaction],
    ledger: Sequence[Transaction],
    matcher: Matcher | None = None,
):
    matcher = matcher or ExactMatcher()
    return matcher.match(statement, ledger)
