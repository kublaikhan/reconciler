from __future__ import annotations

import csv
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Transaction:
    """Represents a single transaction.

    Attributes
    ----------
    data: Raw column mapping for the transaction. Used for pretty printing.
    amount: Paid amount for the transaction.
    date: Parsed date if available.
    description: Human readable description for filtering and matching.
    """

    data: Dict[str, str]
    amount: Decimal
    date: Optional[date]
    description: str

    def key(self) -> Decimal:
        """Return the key used for matching transactions.

        Matching only considers the amount, ignoring dates or descriptions
        which often differ between the ledger and the statement.
        """
        return self.amount


class TransactionLoader(ABC):
    """Abstract loader interface to support different file formats."""

    @abstractmethod
    def load(
        self,
        path: str,
        amount_col: str,
        date_col: Optional[str] = None,
        description_col: Optional[str] = None,
    ) -> List[Transaction]:
        raise NotImplementedError


class CSVLoader(TransactionLoader):
    """Loads transactions from a CSV file."""

    def load(
        self,
        path: str,
        amount_col: str,
        date_col: Optional[str] = None,
        description_col: Optional[str] = None,
    ) -> List[Transaction]:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            txns: List[Transaction] = []
            for row in reader:
                amount_raw = row.get(amount_col, "0")
                try:
                    amount = Decimal(amount_raw)
                except (InvalidOperation, TypeError):
                    continue
                date_val: Optional[date] = None
                if date_col and row.get(date_col):
                    try:
                        date_val = datetime.fromisoformat(row[date_col]).date()
                    except ValueError:
                        pass
                description = row.get(description_col or "Description", "")
                txns.append(Transaction(row, amount, date_val, description))
        return txns


LOADERS = {
    ".csv": CSVLoader(),
}


def get_loader(path: str) -> TransactionLoader:
    """Return a loader instance based on file extension."""
    _, ext = os.path.splitext(path.lower())
    if ext in LOADERS:
        return LOADERS[ext]
    raise ValueError(f"Unsupported file extension: {ext}")


def load_transactions(
    path: str,
    amount_col: str,
    date_col: Optional[str] = None,
    description_col: Optional[str] = None,
) -> List[Transaction]:
    """Convenience wrapper for loading transactions."""
    loader = get_loader(path)
    return loader.load(path, amount_col, date_col, description_col)
