# reconciler

Reconciles lists of transactions with credit card data.

## Usage

The project exposes a small command line interface. Invoke it with `python -m reconciler.cli` and provide at least one transaction file and a credit card statement:

```bash
python -m reconciler.cli \
  --transactions purchases.csv:Total:Date:Description \
  --statement statement.csv:Amount:Date:Description
```

File specifications are of the form `path[:amount_col[:date_col[:description_col]]]`. This allows files with differing column names to be handled. Multiple `--transactions` options may be supplied to combine several sources.

### Options

* `--ignore TEXT` – ignore statement rows whose description contains the given text. May be repeated.
* `--start YYYY-MM-DD` and `--end YYYY-MM-DD` – limit reconciliation to a time period. If omitted the statement's date range is used.
* `--allow-combined` – enable matching where several ledger entries combine into one statement charge.
* `--statement-charges-positive` – set if the statement lists charges as positive amounts. By default charges are assumed negative and are flipped for matching.

Matching is based solely on transaction amounts, ignoring dates and descriptions. The tool reports transactions that appear only on the statement or only in the provided lists and prints all columns for easy inspection.
