import csv
from collections import defaultdict

INPUT_FILE = 'data/homework_invoices.csv'
OUTPUT_FILE = 'data/high_value_invoices.csv'
HIGH_VALUE_THRESHOLD = 100000


def parse_amount(value):
    """Return float amount or raise ValueError for missing/invalid values."""
    if not value.strip():
        raise ValueError("Missing amount")
    return float(value)


def is_high_value(amount):
    """Business rule 1: amount must be above ₹1,00,000."""
    return amount > HIGH_VALUE_THRESHOLD


def is_valid_vendor(vendor):
    """Business rule 2: vendor name must not be empty."""
    return bool(vendor.strip())


def is_valid_status(status):
    """Business rule 3: only process PENDING invoices."""
    return status.strip().upper() == 'PENDING'


def read_invoices(filepath):
    invoices = []
    with open(filepath, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            invoices.append(row)
    return invoices


def filter_invoices(invoices):
    valid = []
    skipped = 0

    for row in invoices:
        # Failure condition 1: missing or invalid amount
        try:
            amount = parse_amount(row['amount'])
        except ValueError as e:
            print(f"Skipping {row['invoice_id']} — {e}")
            skipped += 1
            continue

        # Failure condition 2: missing vendor
        if not is_valid_vendor(row['vendor']):
            print(f"Skipping {row['invoice_id']} — missing vendor name")
            skipped += 1
            continue

        # Business rule 1: high value only
        if not is_high_value(amount):
            continue

        # Business rule 2: vendor must be present (already checked above)
        # Business rule 3: status must be PENDING
        if not is_valid_status(row['status']):
            continue

        valid.append({**row, 'amount': amount})

    print(f"\nSkipped {skipped} invalid rows.")
    return valid


def write_invoices(invoices, filepath):
    if not invoices:
        print("No high-value invoices to write.")
        return

    fieldnames = ['invoice_id', 'vendor', 'amount', 'status']
    with open(filepath, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(invoices)

    print(f"Written {len(invoices)} high-value invoices to {filepath}")


def group_by_vendor(invoices):
    totals = defaultdict(float)
    for row in invoices:
        totals[row['vendor']] += row['amount']

    print("\n--- Vendor Totals ---")
    for vendor, total in sorted(totals.items(), key=lambda x: -x[1]):
        print(f"  {vendor}: ₹{total:,.2f}")


def main():
    invoices = read_invoices(INPUT_FILE)
    high_value = filter_invoices(invoices)
    write_invoices(high_value, OUTPUT_FILE)
    group_by_vendor(high_value)


main()
